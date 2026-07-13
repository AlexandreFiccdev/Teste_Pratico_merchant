from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .exceptions import BusinessRuleError
from .models import Merchant, MerchantEvent, MerchantStatus
from .serializers import (
    BlockMerchantSerializer,
    MerchantDetailSerializer,
    MerchantListSerializer,
    RejectMerchantSerializer,
)


@extend_schema_view(
    list=extend_schema(responses=MerchantListSerializer(many=True)),
    retrieve=extend_schema(responses=MerchantDetailSerializer),
    create=extend_schema(responses=MerchantDetailSerializer),
    update=extend_schema(responses=MerchantDetailSerializer),
    partial_update=extend_schema(responses=MerchantDetailSerializer),
)
class MerchantViewSet(viewsets.ModelViewSet):
    queryset = Merchant.objects.all().order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "id"]

    def get_serializer_class(self):
        if self.action == "list":
            return MerchantListSerializer
        return MerchantDetailSerializer

    def update(self, request, *args, **kwargs):
        merchant = self.get_object()
        if merchant.status != MerchantStatus.DRAFT:
            raise BusinessRuleError(
                "Só é possível atualizar os dados cadastrais enquanto o "
                "merchant estiver em draft."
            )
        return super().update(request, *args, **kwargs)

    @extend_schema(request=None, responses=MerchantDetailSerializer)
    @action(detail=True, methods=["post"], url_path="submit-for-analysis")
    def submit_for_analysis(self, request, pk=None):
        merchant = self.get_object()
        if merchant.status != MerchantStatus.DRAFT:
            raise BusinessRuleError(
                "Só é possível enviar para análise um merchant em draft."
            )
        merchant.status = MerchantStatus.PENDING_ANALYSIS
        merchant.save(update_fields=["status"])
        MerchantEvent.objects.create(
            merchant=merchant, description="Merchant enviado para análise"
        )
        return Response(MerchantDetailSerializer(merchant).data)

    @extend_schema(request=None, responses=MerchantDetailSerializer)
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        merchant = self.get_object()
        if merchant.status != MerchantStatus.PENDING_ANALYSIS:
            raise BusinessRuleError(
                "Só é possível aprovar um merchant em pending_analysis."
            )
        merchant.status = MerchantStatus.APPROVED
        merchant.save(update_fields=["status"])
        MerchantEvent.objects.create(
            merchant=merchant, description="Merchant aprovado"
        )
        return Response(MerchantDetailSerializer(merchant).data)

    @extend_schema(request=RejectMerchantSerializer, responses=MerchantDetailSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        merchant = self.get_object()
        if merchant.status != MerchantStatus.PENDING_ANALYSIS:
            raise BusinessRuleError(
                "Só é possível rejeitar um merchant em pending_analysis."
            )
        serializer = RejectMerchantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        merchant.status = MerchantStatus.REJECTED
        merchant.save(update_fields=["status"])
        MerchantEvent.objects.create(
            merchant=merchant, description=f"Merchant rejeitado: {reason}"
        )
        return Response(MerchantDetailSerializer(merchant).data)

    @extend_schema(request=BlockMerchantSerializer, responses=MerchantDetailSerializer)
    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        merchant = self.get_object()
        if merchant.status != MerchantStatus.APPROVED:
            raise BusinessRuleError(
                "Só é possível bloquear um merchant approved."
            )
        serializer = BlockMerchantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        merchant.status = MerchantStatus.BLOCKED
        merchant.save(update_fields=["status"])
        MerchantEvent.objects.create(
            merchant=merchant, description=f"Merchant bloqueado: {reason}"
        )
        return Response(MerchantDetailSerializer(merchant).data)
