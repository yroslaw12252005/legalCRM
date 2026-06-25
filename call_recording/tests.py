from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from company.models import Companys

from .models import CallRecording


User = get_user_model()


class CallRecordingViewTests(TestCase):
    def setUp(self):
        self.company_1 = Companys.objects.create(title="Company 1")
        self.company_2 = Companys.objects.create(title="Company 2")

        self.allowed_user = User.objects.create_user(
            username="director_kc",
            password="secret123",
            status="Директор КЦ",
            companys=self.company_1,
        )
        self.blocked_user = User.objects.create_user(
            username="operator_1",
            password="secret123",
            status="Оператор",
            companys=self.company_1,
        )

        self.recording = CallRecording.objects.create(
            companys=self.company_1,
            phone="+79001234567",
            operator_phone="+79007654321",
            external_id="abc123",
            file_name="79001234567_20260625_120000_abc123.mp3",
            file_url="https://example.com/file.mp3",
            s3_key="1_Company_1/Записи/79001234567_20260625_120000_abc123.mp3",
        )
        CallRecording.objects.create(
            companys=self.company_2,
            phone="+79990000000",
            operator_phone="+79991111111",
            external_id="def456",
            file_name="79990000000_20260625_120500_def456.mp3",
            file_url="https://example.com/file2.mp3",
            s3_key="2_Company_2/Записи/79990000000_20260625_120500_def456.mp3",
        )

    def test_allowed_role_sees_company_recordings(self):
        self.client.force_login(self.allowed_user)

        response = self.client.get(reverse("get_calls"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+79001234567")
        self.assertNotContains(response, "+79990000000")

    def test_search_filters_by_phone(self):
        self.client.force_login(self.allowed_user)

        response = self.client.get(reverse("get_calls"), {"phone": "1234567"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+79001234567")

    def test_blocked_role_is_redirected(self):
        self.client.force_login(self.blocked_user)

        response = self.client.get(reverse("get_calls"))

        self.assertEqual(response.status_code, 302)

    def test_download_redirects_to_file_url(self):
        self.client.force_login(self.allowed_user)

        response = self.client.get(reverse("download_call", args=[self.recording.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com/file.mp3")

