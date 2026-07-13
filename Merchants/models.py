from django.db import models

from .validators.CNPJ_validator import normalize_cnpj, validate_cnpj


class MerchantStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_ANALYSIS = "pending_analysis", "Pending analysis"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    BLOCKED = "blocked", "Blocked"


class Merchant(models.Model):
    cnpj = models.CharField(max_length=14, unique=True, validators=[validate_cnpj])
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=MerchantStatus.choices,
        default=MerchantStatus.DRAFT,
    )

    def save(self, *args, **kwargs):
        self.cnpj = normalize_cnpj(self.cnpj)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"


class MerchantEvent(models.Model):
    merchant = models.ForeignKey(
        Merchant, related_name="events", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.description
