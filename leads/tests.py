from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
import base64
import hashlib
import hmac

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.forms import Employees_KCForm
from leads.models import Record
from smart_calendar.models import Booking


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.company_1 = Companys.objects.create(title="Company 1")
        self.company_2 = Companys.objects.create(title="Company 2")

        self.felial_1 = Felial.objects.create(title="Main", cites="Moscow", companys=self.company_1)
        self.felial_2 = Felial.objects.create(title="Main", cites="SPB", companys=self.company_2)

        self.director_1 = User.objects.create_user(
            username="director_1",
            password="test-pass-123",
            status="Директор КЦ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_1 = User.objects.create_user(
            username="operator_1",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_actor = User.objects.create_user(
            username="operator_actor",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_2 = User.objects.create_user(
            username="operator_2",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_2,
            felial=self.felial_2,
        )

        self.record_1 = Record.objects.create(
            name="Lead 1",
            phone="+70000000001",
            description="test",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_2 = Record.objects.create(
            name="Lead 2",
            phone="+70000000002",
            description="test",
            companys=self.company_2,
            felial=self.felial_2,
        )

    def test_employees_form_filters_by_record_company(self):
        form = Employees_KCForm(instance=self.record_1, user=self.director_1, company_id=self.record_1.companys_id)
        self.assertIn(self.operator_1, form.fields["employees_KC"].queryset)
        self.assertNotIn(self.operator_2, form.fields["employees_KC"].queryset)

    def test_record_page_denies_cross_company_access(self):
        self.client.force_login(self.director_1)
        response = self.client.get(reverse("record", args=[self.record_2.id]))
        self.assertEqual(response.status_code, 404)

    def test_record_post_rejects_employee_from_other_company(self):
        self.client.force_login(self.director_1)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_2.id)},
        )
        self.assertEqual(response.status_code, 200)

        self.record_1.refresh_from_db()
        self.assertNotEqual(self.record_1.employees_KC, self.operator_2.username)

    def test_record_post_accepts_employee_from_same_company(self):
        self.client.force_login(self.director_1)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_1.id)},
        )
        self.assertEqual(response.status_code, 200)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.employees_KC, self.operator_1.username)

    def test_record_post_requires_role_for_assignment(self):
        self.client.force_login(self.operator_actor)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_1.id)},
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertNotEqual(self.record_1.employees_KC, self.operator_1.username)

    def test_update_record_rejects_non_director_main_edit(self):
        self.client.force_login(self.operator_actor)
        response = self.client.post(
            reverse("update_record", args=[self.record_1.id]),
            data={
                "action": "update_record",
                "name": "Updated by operator",
                "description": "Changed",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.name, "Lead 1")
        self.assertEqual(self.record_1.description, "test")

    def test_update_record_allows_comment_for_non_director(self):
        self.client.force_login(self.operator_actor)
        response = self.client.post(
            reverse("update_record", args=[self.record_1.id]),
            data={
                "action": "update_comment",
                "work_comment": "Комментарий оператора",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.work_comment, "Комментарий оператора")

    def test_update_record_allows_main_edit_for_kc_director(self):
        self.client.force_login(self.director_1)
        response = self.client.post(
            reverse("update_record", args=[self.record_1.id]),
            data={
                "action": "update_record",
                "name": "Updated by director",
                "description": "Director description",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.name, "Updated by director")
        self.assertEqual(self.record_1.description, "Director description")

    def test_record_page_hides_come_buttons_without_booking(self):
        manager = User.objects.create_user(
            username="manager_1",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_1.status = "Запись в офис"
        self.record_1.save(update_fields=["status"])

        self.client.force_login(manager)
        response = self.client.get(reverse("record", args=[self.record_1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Статус прихода")
        self.assertNotContains(response, "Дошел")
        self.assertNotContains(response, "Не дошел")

    def test_record_page_shows_come_buttons_with_booking(self):
        manager = User.objects.create_user(
            username="manager_2",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_1.status = "Запись в офис"
        self.record_1.save(update_fields=["status"])
        Booking.objects.create(
            client=self.record_1,
            date="2026-03-16",
            time="10:30",
            companys=self.company_1,
            felial=self.felial_1,
            registrar=manager,
        )

        self.client.force_login(manager)
        response = self.client.get(reverse("record", args=[self.record_1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статус прихода")
        self.assertContains(response, "Дошел")
        self.assertContains(response, "Не дошел")
class NovofonWebhookTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company 1")
        self.other_company = Companys.objects.create(title="Company 2")
        self.felial_1 = Felial.objects.create(title="Felial 1", cites="Moscow", companys=self.company)
        self.felial_2 = Felial.objects.create(title="Felial 2", cites="Moscow", companys=self.company)
        self.felial_3 = Felial.objects.create(title="Felial 3", cites="Moscow", companys=self.company)
        self.felial_4 = Felial.objects.create(title="Felial 4", cites="Moscow", companys=self.company)
        self.felial_5 = Felial.objects.create(title="Felial 5", cites="Moscow", companys=self.company)
        self.url = reverse("novofon_incoming_call_webhook")
        self.secret = "test-novofon-secret"

    def _signature(self, caller_id, called_did, call_start):
        digest = hmac.new(
            self.secret.encode("utf-8"),
            f"{caller_id}{called_did}{call_start}".encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    @patch("leads.views.NOVOFON_API_SECRET", "test-novofon-secret")
    def test_creates_new_record_for_unknown_phone(self):
        payload = {
            "event": "NOTIFY_START",
            "caller_id": "+7 (999) 111-22-33",
            "called_did": "+74951234567",
            "call_start": "1718361000",
        }
        payload["signature"] = self._signature(payload["caller_id"], payload["called_did"], payload["call_start"])

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 201)
        record = Record.objects.get(companys=self.company, phone="+79991112233")
        self.assertEqual(record.where, "Звонок")
        self.assertEqual(record.felial_id, self.felial_5.id)

    @patch("leads.views.NOVOFON_API_SECRET", "test-novofon-secret")
    def test_does_not_create_duplicate_record_for_existing_phone(self):
        Record.objects.create(
            phone="+79991112233",
            companys=self.company,
            felial=self.felial_5,
        )
        payload = {
            "event": "NOTIFY_INTERNAL",
            "caller_id": "8 999 111 22 33",
            "called_did": "+74951234567",
            "call_start": "1718361000",
        }
        payload["signature"] = self._signature(payload["caller_id"], payload["called_did"], payload["call_start"])

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Record.objects.filter(companys=self.company, phone="+79991112233").count(), 1)

    @patch("leads.views.NOVOFON_API_SECRET", "test-novofon-secret")
    def test_rejects_invalid_signature(self):
        response = self.client.post(
            self.url,
            data={
                "event": "NOTIFY_START",
                "caller_id": "+79991112233",
                "called_did": "+74951234567",
                "call_start": "1718361000",
                "signature": "invalid-signature",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Record.objects.filter(companys=self.company, phone="+79991112233").exists())
