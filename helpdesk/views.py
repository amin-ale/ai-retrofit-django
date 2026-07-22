from django.http import JsonResponse


def home(request):
    return JsonResponse(
        {
            "app": "helpdesk",
            "note": "Existing product. The AI copilot retrofit lives under /copilot/.",
        }
    )
