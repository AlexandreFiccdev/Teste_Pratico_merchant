from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Merchant, MerchantEvent
from .validators.CNPJ_validator import normalize_cnpj, validate_cnpj


class MerchantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantEvent
        fields = ["id", "description", "created_at"]
        read_only_fields = fields


class CNPJField(serializers.CharField):
    """Accepts a CNPJ with or without mask, normalizing it (digits/letters
    only, uppercased) before validators or uniqueness checks run, so a
    masked and unmasked version of the same CNPJ are always recognized as
    the same value."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return normalize_cnpj(value)


class MerchantFieldsMixin(serializers.Serializer):
    cnpj = CNPJField(
        max_length=14,
        validators=[
            validate_cnpj,
            UniqueValidator(
                queryset=Merchant.objects.all(),
                message="Já existe um merchant com esse CNPJ.",
            ),
        ],
        error_messages={
            "required": "CNPJ é obrigatório.",
            "blank": "CNPJ é obrigatório.",
        },
    )
    razao_social = serializers.CharField(
        error_messages={
            "required": "Razão social é obrigatória.",
            "blank": "Razão social é obrigatória.",
        },
    )
    email = serializers.EmailField(
        error_messages={
            "required": "E-mail é obrigatório.",
            "blank": "E-mail é obrigatório.",
        },
    )


class MerchantListSerializer(MerchantFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = [
            "id",
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "email",
            "telefone",
            "created_at",
            "status",
        ]
        read_only_fields = ["id", "created_at", "status"]


class MerchantDetailSerializer(MerchantFieldsMixin, serializers.ModelSerializer):
    events = MerchantEventSerializer(many=True, read_only=True)

    class Meta:
        model = Merchant
        fields = [
            "id",
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "email",
            "telefone",
            "created_at",
            "status",
            "events",
        ]
        read_only_fields = ["id", "created_at", "status"]


class RejectMerchantSerializer(serializers.Serializer):
    reason = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "required": "Informe um motivo para rejeitar.",
            "blank": "Informe um motivo para rejeitar.",
        },
    )


class BlockMerchantSerializer(serializers.Serializer):
    reason = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "required": "Informe um motivo para bloquear.",
            "blank": "Informe um motivo para bloquear.",
        },
    )
