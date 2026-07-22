import json

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services import ask_data, summarize
from .services.budget import BudgetExceeded, remaining_tokens
from .services.flags import FeatureDisabled, is_enabled
from .services.semantic_search import search
from .services.sql_guard import SqlGuardError
from .services.summarize import TicketNotFound


def _body(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def _resolve(request, data):
    tenant_raw = data.get("tenant") or request.headers.get("X-Tenant-Id")
    tenant_id = int(tenant_raw) if tenant_raw is not None else None
    user_id = request.user.id if request.user.is_authenticated else None
    return tenant_id, user_id


def _sse(events):
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


def panel(request):
    return render(request, "copilot/panel.html")


@require_GET
def status(request):
    tenant_raw = request.GET.get("tenant") or request.headers.get("X-Tenant-Id")
    if tenant_raw is None:
        return JsonResponse({"error": "tenant is required"}, status=400)
    tenant_id = int(tenant_raw)
    enabled = is_enabled(tenant_id)
    return JsonResponse({"enabled": enabled, "remaining_tokens": remaining_tokens(tenant_id)})


@csrf_exempt
@require_POST
def search_view(request):
    data = _body(request)
    tenant_id, _ = _resolve(request, data)
    query = (data.get("query") or "").strip()
    if tenant_id is None or not query:
        return JsonResponse({"error": "tenant and query are required"}, status=400)
    try:
        results = search(tenant_id, query)
    except FeatureDisabled:
        return JsonResponse({"error": "copilot disabled"}, status=404)
    return JsonResponse({"results": results})


@csrf_exempt
@require_POST
def ask_view(request):
    data = _body(request)
    tenant_id, user_id = _resolve(request, data)
    question = (data.get("question") or "").strip()
    if tenant_id is None or not question:
        return JsonResponse({"error": "tenant and question are required"}, status=400)
    try:
        prep = ask_data.prepare_ask(tenant_id, question, user_id)
    except FeatureDisabled:
        return JsonResponse({"error": "copilot disabled"}, status=404)
    except BudgetExceeded as exc:
        return JsonResponse({"error": str(exc), "limit": exc.limit}, status=429)
    except SqlGuardError as exc:
        return JsonResponse({"error": "query blocked by guardrail", "reason": str(exc)}, status=400)
    response = StreamingHttpResponse(
        _sse(ask_data.stream_answer(prep)), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    return response


@csrf_exempt
@require_POST
def summarize_view(request):
    data = _body(request)
    tenant_id, user_id = _resolve(request, data)
    ticket_raw = data.get("ticket_id")
    if tenant_id is None or ticket_raw is None:
        return JsonResponse({"error": "tenant and ticket_id are required"}, status=400)
    try:
        prep = summarize.prepare_summary(tenant_id, int(ticket_raw), user_id)
    except FeatureDisabled:
        return JsonResponse({"error": "copilot disabled"}, status=404)
    except BudgetExceeded as exc:
        return JsonResponse({"error": str(exc), "limit": exc.limit}, status=429)
    except TicketNotFound as exc:
        return JsonResponse({"error": str(exc)}, status=404)
    response = StreamingHttpResponse(
        _sse(summarize.stream_from_prep(prep)), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    return response
