from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Merchant, MerchantStatus
from .factories import merchant_payload


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
