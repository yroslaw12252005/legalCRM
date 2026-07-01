from unittest.mock import MagicMock, patch

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
            s3_key="call_recordings/1/2026/06/25/79001234567_20260625_120000_abc123.mp3",
        )
        CallRecording.objects.create(
            companys=self.company_2,
            phone="+79990000000",
            operator_phone="+79991111111",
            external_id="def456",
            file_name="79990000000_20260625_120500_def456.mp3",
            file_url="https://example.com/file2.mp3",
            s3_key="call_recordings/2/2026/06/25/79990000000_20260625_120500_def456.mp3",
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

    @patch("call_recording.views.urlopen")
    def test_download_returns_attachment_response(self, mock_urlopen):
        self.client.force_login(self.allowed_user)
        remote_file = MagicMock()
        remote_file.read.return_value = b"fake-audio"
        mock_urlopen.return_value.__enter__.return_value = remote_file

        response = self.client.get(reverse("download_call", args=[self.recording.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"fake-audio")
        self.assertEqual(response["Content-Type"], "application/octet-stream")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn(self.recording.file_name, response["Content-Disposition"])

    @patch("call_recording.views.urlopen")
    def test_download_uses_file_url_when_s3_key_does_not_match(self, mock_urlopen):
        self.client.force_login(self.allowed_user)
        remote_file = MagicMock()
        remote_file.read.return_value = b"audio-from-file-url"
        mock_urlopen.return_value.__enter__.return_value = remote_file
        self.recording.s3_key = "other/path/file.mp3"
        self.recording.save(update_fields=["s3_key"])

        response = self.client.get(reverse("download_call", args=[self.recording.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"audio-from-file-url")
        mock_urlopen.assert_called_once_with("https://example.com/file.mp3")
