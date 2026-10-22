from io import BytesIO
from unittest.mock import patch
from urllib.parse import quote

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record, RecordDocument


class ClientCabinetDocumentsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.other_company = Companys.objects.create(title="Другая компания")
        self.branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.company)
        self.other_branch = Felial.objects.create(
            title="Главный",
            cites="Тула",
            companys=self.other_company,
        )
        self.manager = User.objects.create_user(
            username="manager_client_cabinet",
            password="password",
            status="Менеджер",
            companys=self.company,
            felial=self.branch,
        )
        self.record = Record.objects.create(
            name="Клиент",
            companys=self.company,
            felial=self.branch,
        )
        self.other_record = Record.objects.create(
            name="Чужой клиент",
            companys=self.other_company,
            felial=self.other_branch,
        )

    def test_client_cabinet_shows_uploaded_documents_and_download_link(self):
        document = RecordDocument.objects.create(
            record=self.record,
            file_name="Договор.pdf",
            file_url="https://storage.example.test/contract.pdf",
            s3_key="1/contract.pdf",
        )
        response = self.client.get(reverse("client_portal", args=[self.record.client_access_token]))

        self.assertContains(response, "Документы")
        self.assertContains(response, "Договор.pdf")
        self.assertContains(
            response,
            reverse(
                "client_document_download",
                args=[self.record.client_access_token, document.id],
            ),
        )
        self.assertContains(response, "Скачать")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_client_cabinet_shows_empty_documents_message(self):
        response = self.client.get(reverse("client_portal", args=[self.record.client_access_token]))

        self.assertContains(response, "Документы ещё не загружены")

    def test_client_cabinet_does_not_open_record_from_other_company(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("client_inform", args=[self.other_record.id]))

        self.assertEqual(response.status_code, 404)

    def test_client_portal_rejects_unknown_token(self):
        response = self.client.get(
            reverse("client_portal", args=["11111111-1111-4111-8111-111111111111"])
        )

        self.assertEqual(response.status_code, 404)

    def test_client_cabinet_shows_legacy_document(self):
        self.record.doc = "https://storage.example.test/legacy.pdf"
        self.record.save(update_fields=["doc"])

        response = self.client.get(reverse("client_portal", args=[self.record.client_access_token]))

        self.assertContains(response, "Документ из старой карточки")
        self.assertContains(response, self.record.doc)
        self.assertNotContains(response, "Документы ещё не загружены")

    @patch("leads.document_download.urlopen")
    def test_client_can_download_own_document_by_token(self, mocked_urlopen):
        mocked_urlopen.return_value = BytesIO(b"document-content")
        document = RecordDocument.objects.create(
            record=self.record,
            file_name="Договор.pdf",
            file_url="https://storage.example.test/contract.pdf",
        )

        response = self.client.get(
            reverse(
                "client_document_download",
                args=[self.record.client_access_token, document.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"document-content")
        self.assertIn(quote("Договор.pdf"), response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "private, no-store")

    @patch("leads.document_download.urlopen")
    def test_client_cannot_download_document_with_another_token(self, mocked_urlopen):
        document = RecordDocument.objects.create(
            record=self.other_record,
            file_name="Чужой договор.pdf",
            file_url="https://storage.example.test/other.pdf",
        )

        response = self.client.get(
            reverse(
                "client_document_download",
                args=[self.record.client_access_token, document.id],
            )
        )

        self.assertEqual(response.status_code, 404)
        mocked_urlopen.assert_not_called()
