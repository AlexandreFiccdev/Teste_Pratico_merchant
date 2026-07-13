from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Merchant, MerchantStatus


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
