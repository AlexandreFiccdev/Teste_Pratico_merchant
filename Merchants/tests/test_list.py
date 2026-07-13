from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Merchant, MerchantStatus


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
