from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Merchant, MerchantStatus


class MerchantStatusTransitionTests(APITestCase):
    def setUp(self):
        self.draft = Merchant.objects.create(
            cnpj="11222333000181",
            razao_social="Draft LTDA",
            email="draft@exemplo.com",
        )

    def submit_for_analysis(self, merchant):
        return self.client.post(
            reverse("merchant-submit-for-analysis", args=[merchant.id])
        )

    def test_submit_for_analysis_from_draft(self):
        response = self.submit_for_analysis(self.draft)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, MerchantStatus.PENDING_ANALYSIS)
        self.assertEqual(self.draft.events.count(), 1)
        self.assertEqual(
            self.draft.events.first().description, "Merchant enviado para análise"
        )

    def test_submit_for_analysis_fails_outside_draft(self):
        self.submit_for_analysis(self.draft)
        response = self.submit_for_analysis(self.draft)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_approve_from_pending_analysis(self):
        self.submit_for_analysis(self.draft)
        response = self.client.post(reverse("merchant-approve", args=[self.draft.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, MerchantStatus.APPROVED)
        self.assertEqual(
            self.draft.events.last().description, "Merchant aprovado"
        )

    def test_approve_fails_when_not_pending_analysis(self):
        response = self.client.post(reverse("merchant-approve", args=[self.draft.id]))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_reject_from_pending_analysis_requires_reason(self):
        self.submit_for_analysis(self.draft)
        response = self.client.post(
            reverse("merchant-reject", args=[self.draft.id]), {}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_from_pending_analysis(self):
        self.submit_for_analysis(self.draft)
        response = self.client.post(
            reverse("merchant-reject", args=[self.draft.id]),
            {"reason": "Documentação inválida"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, MerchantStatus.REJECTED)
        self.assertEqual(
            self.draft.events.last().description,
            "Merchant rejeitado: Documentação inválida",
        )

    def test_reject_fails_when_not_pending_analysis(self):
        response = self.client.post(
            reverse("merchant-reject", args=[self.draft.id]),
            {"reason": "Qualquer motivo"},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_block_approved_merchant_requires_reason(self):
        self.submit_for_analysis(self.draft)
        self.client.post(reverse("merchant-approve", args=[self.draft.id]))

        response = self.client.post(
            reverse("merchant-block", args=[self.draft.id]), {}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_block_approved_merchant(self):
        self.submit_for_analysis(self.draft)
        self.client.post(reverse("merchant-approve", args=[self.draft.id]))

        response = self.client.post(
            reverse("merchant-block", args=[self.draft.id]),
            {"reason": "Suspeita de fraude"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, MerchantStatus.BLOCKED)
        self.assertEqual(
            self.draft.events.last().description,
            "Merchant bloqueado: Suspeita de fraude",
        )

    def test_block_fails_when_not_approved(self):
        response = self.client.post(
            reverse("merchant-block", args=[self.draft.id]),
            {"reason": "Qualquer motivo"},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_full_timeline_is_recorded_in_order(self):
        self.submit_for_analysis(self.draft)
        self.client.post(reverse("merchant-approve", args=[self.draft.id]))
        self.client.post(
            reverse("merchant-block", args=[self.draft.id]),
            {"reason": "Suspeita de fraude"},
        )

        descriptions = list(
            self.draft.events.order_by("created_at").values_list(
                "description", flat=True
            )
        )
        self.assertEqual(
            descriptions,
            [
                "Merchant enviado para análise",
                "Merchant aprovado",
                "Merchant bloqueado: Suspeita de fraude",
            ],
        )
