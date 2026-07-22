from django.conf import settings
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "helpdesk_tenant"

    def __str__(self):
        return self.name


class Customer(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="customers")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    plan = models.CharField(max_length=40, default="free")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "helpdesk_customer"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("pending", "Pending"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="tickets")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="tickets")
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    subject = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="normal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "helpdesk_ticket"

    def __str__(self):
        return self.subject


class TicketMessage(models.Model):
    AUTHOR_CHOICES = [
        ("customer", "Customer"),
        ("agent", "Agent"),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    author_kind = models.CharField(max_length=20, choices=AUTHOR_CHOICES)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "helpdesk_ticketmessage"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author_kind} message on ticket {self.ticket_id}"
