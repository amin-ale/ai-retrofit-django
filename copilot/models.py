from django.db import models


class CopilotTenantConfig(models.Model):
    tenant_id = models.IntegerField(unique=True)
    enabled = models.BooleanField(default=True)
    daily_token_budget = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "copilot_tenant_config"


class CopilotEmbedding(models.Model):
    tenant_id = models.IntegerField()
    source_table = models.CharField(max_length=100)
    source_pk = models.IntegerField()
    content = models.TextField()
    vector = models.JSONField()
    model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "copilot_embedding"
        indexes = [
            models.Index(fields=["tenant_id", "source_table"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_table", "source_pk"],
                name="copilot_embedding_source_unique",
            )
        ]


class CopilotResponseCache(models.Model):
    cache_key = models.CharField(max_length=64, unique=True)
    feature = models.CharField(max_length=40)
    response_text = models.TextField()
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "copilot_response_cache"


class CopilotUsageLog(models.Model):
    tenant_id = models.IntegerField()
    user_id = models.IntegerField(null=True, blank=True)
    feature = models.CharField(max_length=40)
    model = models.CharField(max_length=100)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_hit = models.BooleanField(default=False)
    prompt_redacted = models.TextField(blank=True)
    response_preview = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "copilot_usage_log"
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
        ]
