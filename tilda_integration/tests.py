import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import TildaIdempotencyKey, TildaIntegration
from .services import hash_secret


class TildaWebhookTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Webhook company")
        self.branch = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.secret = "tld_test-secret"
        self.integration = TildaIntegration.objects.create(
            company=self.company,
            branch=self.branch,
            title="Website",
            secret_hash=hash_secret(self.secret),
        )
        self.url = reverse("tilda_webhook", args=[self.integration.public_id])

    def post(self, data, token=None):
        headers = {}
        if token is not None:
            headers["HTTP_X_TILDA_TOKEN"] = token
        return self.client.post(self.url, data=data, **headers)

    def test_connection_check_requires_key_and_does_not_create_lead(self):
        forbidden = self.post({"test": "test"})
        accepted = self.post({"test": "test"}, self.secret)

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.content, b"ok")
        self.assertFalse(Record.objects.exists())

    def test_creates_lead_in_integration_company_and_branch(self):
        response = self.post(
            {
                "tranid": "467251:8442970",
                "formid": "form48844953",
                "Name": "Мария",
                "Phone": "8 (999) 111-22-33",
                "Email": "MARIA@EXAMPLE.COM",
                "Comments": "Нужна консультация",
            },
            self.secret,
        )

        self.assertEqual(response.status_code, 200)
        lead = Record.objects.get()
        self.assertEqual(lead.companys, self.company)
        self.assertEqual(lead.felial, self.branch)
        self.assertEqual(lead.name, "Мария")
        self.assertEqual(lead.phone, "+79991112233")
        self.assertEqual(lead.email, "maria@example.com")
        self.assertEqual(lead.where, "Tilda")
        self.assertIn("Comments: Нужна консультация", lead.description)

    def test_payload_cannot_switch_company_or_branch(self):
        other_company = Companys.objects.create(title="Other company")
        other_branch = Felial.objects.create(title="Other", cites="Kazan", companys=other_company)

        response = self.post(
            {
                "tranid": "tenant-isolation",
                "Name": "Иван",
                "Phone": "+79990000000",
                "id_company": str(other_company.id),
                "id_felial": str(other_branch.id),
            },
            self.secret,
        )

        self.assertEqual(response.status_code, 200)
        lead = Record.objects.get()
        self.assertEqual(lead.companys, self.company)
        self.assertEqual(lead.felial, self.branch)
        self.assertNotIn("id_company", lead.description)

    def test_duplicate_tranid_returns_ok_without_second_lead(self):
        payload = {"tranid": "same-id", "Name": "Анна", "Phone": "+79990000001"}

        first = self.post(payload, self.secret)
        second = self.post(payload, self.secret)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Record.objects.count(), 1)
        self.assertEqual(TildaIdempotencyKey.objects.count(), 1)
        self.integration.refresh_from_db()
        self.assertEqual(self.integration.total_duplicates, 1)

    def test_rejects_form_outside_allow_list(self):
        self.integration.allowed_form_ids = ["form-allowed"]
        self.integration.save(update_fields=["allowed_form_ids"])

        response = self.post(
            {"tranid": "wrong-form", "formid": "form-other", "Phone": "+79990000002"},
            self.secret,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"form_not_allowed")
        self.assertFalse(Record.objects.exists())

    def test_accepts_json(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"tranid": "json-id", "name": "JSON client", "phone": "+79990000003"}),
            content_type="application/json",
            HTTP_X_TILDA_TOKEN=self.secret,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Record.objects.filter(name="JSON client").exists())

    def test_token_can_be_sent_as_post_field_and_is_not_saved(self):
        response = self.post(
            {"tranid": "post-token", "token": self.secret, "Phone": "+79990000004"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.secret, Record.objects.get().description)

    def test_rejects_request_larger_than_limit(self):
        response = self.client.post(
            self.url,
            data={"Name": "Large request"},
            HTTP_X_TILDA_TOKEN=self.secret,
            CONTENT_LENGTH=str(256 * 1024 + 1),
        )
        self.assertEqual(response.status_code, 413)

    def test_rate_limit_is_enforced_per_integration(self):
        with patch("tilda_integration.views.WEBHOOK_RATE_LIMIT", 2):
            first = self.post({"test": "test"}, self.secret)
            second = self.post({"test": "test"}, self.secret)
            limited = self.post({"test": "test"}, self.secret)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(limited.status_code, 429)

    def test_custom_field_mapping_is_used(self):
        self.integration.field_mapping = {
            "name": ["client_fio"],
            "phone": ["mobile_number"],
            "email": [],
            "comment": ["question"],
        }
        self.integration.save(update_fields=["field_mapping"])

        response = self.post(
            {
                "tranid": "custom-fields",
                "client_fio": "Пётр",
                "mobile_number": "+79990000005",
                "question": "Вопрос клиента",
            },
            self.secret,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Record.objects.filter(name="Пётр", phone="+79990000005").exists())


class TildaIntegrationManagementTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Managed company")
        self.branch = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.admin = User.objects.create_user(
            username="integration_admin",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )
        self.manager = User.objects.create_user(
            username="integration_manager",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.branch,
        )

    def test_admin_can_create_integration_and_sees_secret_once(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("tilda_integration_create"),
            {
                "title": "Main form",
                "branch": self.branch.id,
                "name_fields": "name, Name",
                "phone_fields": "phone, Phone",
                "email_fields": "email, Email",
                "comment_fields": "comment, Comments",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        integration = TildaIntegration.objects.get(company=self.company)
        self.assertContains(response, "tld_")
        self.assertContains(response, str(integration.public_id))
        self.assertNotIn("tld_", integration.secret_hash)

    def test_secret_rotation_has_ten_minute_overlap(self):
        integration = TildaIntegration.objects.create(
            company=self.company,
            branch=self.branch,
            title="Rotation",
            secret_hash=hash_secret("old-secret"),
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("tilda_integration_rotate_secret", args=[integration.id]))
        new_secret = response.context["new_secret"]
        webhook_url = reverse("tilda_webhook", args=[integration.public_id])

        old_response = self.client.post(
            webhook_url,
            {"test": "test"},
            HTTP_X_TILDA_TOKEN="old-secret",
        )
        new_response = self.client.post(
            webhook_url,
            {"test": "test"},
            HTTP_X_TILDA_TOKEN=new_secret,
        )

        self.assertEqual(old_response.status_code, 200)
        self.assertEqual(new_response.status_code, 200)

    def test_non_admin_cannot_open_management_page(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("tilda_integration_list"))
        self.assertEqual(response.status_code, 404)
