from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from call_recording.models import CallRecording
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
            status="Р”РёСЂРµРєС‚РѕСЂ РљР¦",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_1 = User.objects.create_user(
            username="operator_1",
            password="test-pass-123",
            status="РћРїРµСЂР°С‚РѕСЂ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_actor = User.objects.create_user(
            username="operator_actor",
            password="test-pass-123",
            status="РћРїРµСЂР°С‚РѕСЂ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_2 = User.objects.create_user(
            username="operator_2",
            password="test-pass-123",
            status="РћРїРµСЂР°С‚РѕСЂ",
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
                "work_comment": "РљРѕРјРјРµРЅС‚Р°СЂРёР№ РѕРїРµСЂР°С‚РѕСЂР°",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.work_comment, "РљРѕРјРјРµРЅС‚Р°СЂРёР№ РѕРїРµСЂР°С‚РѕСЂР°")

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
            status="РњРµРЅРµРґР¶РµСЂ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_1.status = "Р—Р°РїРёСЃСЊ РІ РѕС„РёСЃ"
        self.record_1.save(update_fields=["status"])

        self.client.force_login(manager)
        response = self.client.get(reverse("record", args=[self.record_1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "РЎС‚Р°С‚СѓСЃ РїСЂРёС…РѕРґР°")
        self.assertNotContains(response, "Р”РѕС€РµР»")
        self.assertNotContains(response, "РќРµ РґРѕС€РµР»")

    def test_record_page_shows_come_buttons_with_booking(self):
        manager = User.objects.create_user(
            username="manager_2",
            password="test-pass-123",
            status="РњРµРЅРµРґР¶РµСЂ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_1.status = "Р—Р°РїРёСЃСЊ РІ РѕС„РёСЃ"
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
        self.assertContains(response, "РЎС‚Р°С‚СѓСЃ РїСЂРёС…РѕРґР°")
        self.assertContains(response, "Р”РѕС€РµР»")
        self.assertContains(response, "РќРµ РґРѕС€РµР»")

    def test_record_page_shows_call_recordings_matched_without_country_code(self):
        CallRecording.objects.create(
            companys=self.company_1,
            phone="+7 (000) 000-00-01",
            operator_phone="+79990000000",
            external_id="match-1",
            file_name="match-1.mp3",
            file_url="https://example.com/match-1.mp3",
            s3_key="call_recordings/1/match-1.mp3",
        )
        CallRecording.objects.create(
            companys=self.company_1,
            phone="8 000 000 00 01",
            operator_phone="+79990000000",
            external_id="match-2",
            file_name="match-2.mp3",
            file_url="https://example.com/match-2.mp3",
            s3_key="call_recordings/1/match-2.mp3",
        )
        CallRecording.objects.create(
            companys=self.company_1,
            phone="+70000000009",
            operator_phone="+79990000000",
            external_id="other-phone",
            file_name="other-phone.mp3",
            file_url="https://example.com/other-phone.mp3",
            s3_key="call_recordings/1/other-phone.mp3",
        )
        CallRecording.objects.create(
            companys=self.company_2,
            phone="+70000000001",
            operator_phone="+79990000000",
            external_id="other-company",
            file_name="other-company.mp3",
            file_url="https://example.com/other-company.mp3",
            s3_key="call_recordings/2/other-company.mp3",
        )

        self.client.force_login(self.director_1)
        response = self.client.get(reverse("record", args=[self.record_1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Аудиозаписи клиента")
        self.assertContains(response, "match-1.mp3")
        self.assertContains(response, "match-2.mp3")
        self.assertNotContains(response, "other-phone.mp3")
        self.assertNotContains(response, "other-company.mp3")
