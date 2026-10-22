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
        self.client.force_login(self.manager)

        response = self.client.get(reverse("client_inform", args=[self.record.id]))

        self.assertContains(response, "Документы")
        self.assertContains(response, "Договор.pdf")
        self.assertContains(response, reverse("download_document", args=[document.id]))
        self.assertContains(response, "Скачать")

    def test_client_cabinet_shows_empty_documents_message(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("client_inform", args=[self.record.id]))

        self.assertContains(response, "Документы ещё не загружены")

    def test_client_cabinet_does_not_open_record_from_other_company(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("client_inform", args=[self.other_record.id]))

        self.assertEqual(response.status_code, 404)
