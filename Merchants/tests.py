from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .models import Merchant, MerchantStatus


def merchant_payload(**overrides):
    payload = {
        "cnpj": "11222333000181",
        "razao_social": "Comercio Exemplo LTDA",
        "nome_fantasia": "Exemplo",
        "email": "contato@exemplo.com",
        "telefone": "11999998888",
    }
    payload.update(overrides)
    return payload


class MerchantCreateTests(APITestCase):
    def test_create_merchant_with_valid_data(self):
        response = self.client.post(reverse("merchant-list"), merchant_payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], MerchantStatus.DRAFT)
        self.assertEqual(Merchant.objects.count(), 1)

    def test_cnpj_is_required(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_razao_social_is_required(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(razao_social="")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("razao_social", response.data)

    def test_email_is_required(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(email="")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_cnpj_must_be_unique(self):
        self.client.post(reverse("merchant-list"), merchant_payload())
        response = self.client.post(reverse("merchant-list"), merchant_payload())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_cnpj_must_have_14_digits(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="123")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_cnpj_must_have_valid_check_digits(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="11222333000199")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_cnpj_accepts_valid_alphanumeric_format(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="12ABCD5F000159")
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cnpj_rejects_alphanumeric_with_invalid_check_digits(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="12ABCD5F000100")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_cnpj_rejects_letters_in_check_digit_positions(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="12ABCD5F0001A9")
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_cnpj_is_case_insensitive(self):
        response = self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="12abcd5f000159")
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cnpj_with_mask_is_stored_without_mask(self):
        response = self.client.post(
            reverse("merchant-list"),
            merchant_payload(cnpj="11.222.333/0001-81"),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cnpj"], "11222333000181")
        merchant = Merchant.objects.get()
        self.assertEqual(merchant.cnpj, "11222333000181")

    def test_cnpj_masked_and_unmasked_are_treated_as_duplicate(self):
        self.client.post(
            reverse("merchant-list"), merchant_payload(cnpj="11222333000181")
        )
        response = self.client.post(
            reverse("merchant-list"),
            merchant_payload(cnpj="11.222.333/0001-81"),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)

    def test_client_cannot_set_initial_status(self):
        response = self.client.post(
            reverse("merchant-list"),
            merchant_payload(status=MerchantStatus.APPROVED),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], MerchantStatus.DRAFT)


class MerchantRetrieveListTests(APITestCase):
    def setUp(self):
        self.draft = Merchant.objects.create(
            cnpj="11222333000181",
            razao_social="Draft LTDA",
            email="draft@exemplo.com",
        )
        self.approved = Merchant.objects.create(
            cnpj="11222333000262",
            razao_social="Approved LTDA",
            email="approved@exemplo.com",
            status=MerchantStatus.APPROVED,
        )

    def test_retrieve_merchant_by_id(self):
        response = self.client.get(
            reverse("merchant-detail", args=[self.draft.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cnpj"], self.draft.cnpj)
        self.assertIn("events", response.data)

    def test_retrieve_nonexistent_merchant_returns_404(self):
        response = self.client.get(reverse("merchant-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_merchants(self):
        response = self.client.get(reverse("merchant-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_merchants_filtered_by_status(self):
        response = self.client.get(
            reverse("merchant-list"), {"status": MerchantStatus.APPROVED}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.approved.id)


class MerchantUpdateTests(APITestCase):
    def setUp(self):
        self.draft = Merchant.objects.create(
            cnpj="11222333000181",
            razao_social="Draft LTDA",
            email="draft@exemplo.com",
        )
        self.approved = Merchant.objects.create(
            cnpj="11222333000262",
            razao_social="Approved LTDA",
            email="approved@exemplo.com",
            status=MerchantStatus.APPROVED,
        )

    def test_update_allowed_while_draft(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"razao_social": "Nova Razao Social"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.razao_social, "Nova Razao Social")

    def test_update_forbidden_outside_draft(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.approved.id]),
            {"razao_social": "Nova Razao Social"},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.approved.refresh_from_db()
        self.assertEqual(self.approved.razao_social, "Approved LTDA")

    def test_update_cnpj_to_already_existing_value_fails(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"cnpj": self.approved.cnpj},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.cnpj, "11222333000181")

    def test_update_cnpj_with_invalid_format_fails(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"cnpj": "123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.cnpj, "11222333000181")

    def test_update_cnpj_with_blank_value_fails(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"cnpj": ""},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cnpj", response.data)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.cnpj, "11222333000181")

    def test_update_cnpj_keeping_same_value_is_allowed(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"cnpj": self.draft.cnpj, "razao_social": "Nova Razao Social"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.razao_social, "Nova Razao Social")

    def test_update_with_invalid_email_fails(self):
        response = self.client.patch(
            reverse("merchant-detail", args=[self.draft.id]),
            {"email": "nao-e-um-email"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.email, "draft@exemplo.com")


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
