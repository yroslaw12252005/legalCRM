from datetime import timedelta
from types import SimpleNamespace

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from company.demo import cleanup_expired_demo_companies
from company.models import Companys
from cost.views import _salary_calculation, _selected_period
from leads.models import Record
from todolist.models import ToDoList


class LandingPageTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_landing_contains_brand_content_and_seo_metadata(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rossCRM")
        self.assertContains(response, "CRM-система для юридического бизнеса")
        self.assertContains(response, '<link rel="canonical"', html=False)
        self.assertContains(response, 'type="application/ld+json"', html=False)
        self.assertContains(response, "FAQPage")
        self.assertContains(response, 'img/logorossCRM.jpg')

    def test_landing_links_to_login_and_company_registration(self):
        response = self.client.get(reverse("index"))

        self.assertContains(response, f'href="{reverse("all_leads")}"', html=False)
        self.assertContains(response, f'href="{reverse("reg_company")}"', html=False)
        self.assertContains(response, f'href="{reverse("demo_landing")}"', html=False)

    def test_robots_points_to_sitemap_and_hides_private_sections(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")
        self.assertContains(response, "Disallow: /all-leads/")

    def test_sitemap_contains_public_landing_page(self):
        response = self.client.get(reverse("sitemap_xml"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/xml"))
        self.assertContains(response, "<loc>http://testserver/</loc>")


class PublicDemoTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_demo_landing_is_public(self):
        response = self.client.get(reverse("demo_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Создать мою демокомпанию")
        self.assertContains(response, "Сессия 2 часа")

    def test_start_creates_isolated_company_and_logs_in(self):
        response = self.client.post(reverse("demo_start"))

        self.assertRedirects(
            response,
            f"{reverse('current_applications')}?tour=1",
            fetch_redirect_response=False,
        )
        user = User.objects.get(pk=int(self.client.session["_auth_user_id"]))
        self.assertTrue(user.companys.is_demo)
        self.assertGreater(user.companys.demo_expires_at, timezone.now())
        self.assertEqual(Record.objects.filter(companys=user.companys).count(), 36)
        self.assertTrue(ToDoList.objects.filter(user=user.id).exists())
        self.assertTrue(user.should_start_onboarding)
        selected = _selected_period(SimpleNamespace(GET={}))
        representative = User.objects.filter(
            companys=user.companys,
            status="Представитель",
        ).first()
        salary = _salary_calculation(
            representative,
            selected["period_start"],
            selected["period_end"],
        )
        self.assertGreater(salary["salary"], 0)

        tasks_response = self.client.get(reverse("todolist"))
        self.assertContains(tasks_response, "Демонстрационная задача")
        self.assertNotContains(tasks_response, "Подписка истечёт")

    def test_each_visitor_gets_a_separate_company(self):
        other_client = self.client_class()

        self.client.post(reverse("demo_start"), REMOTE_ADDR="192.0.2.10")
        other_client.post(reverse("demo_start"), REMOTE_ADDR="192.0.2.11")

        first_user = User.objects.get(pk=int(self.client.session["_auth_user_id"]))
        second_user = User.objects.get(pk=int(other_client.session["_auth_user_id"]))
        self.assertNotEqual(first_user.companys_id, second_user.companys_id)
        self.assertFalse(
            Record.objects.filter(
                companys=first_user.companys,
                lawyer__companys=second_user.companys,
            ).exists()
        )

    def test_exit_deletes_only_current_demo_company(self):
        regular_company = Companys.objects.create(title="Обычная компания")
        self.client.post(reverse("demo_start"))
        demo_user = User.objects.get(pk=int(self.client.session["_auth_user_id"]))
        demo_company_id = demo_user.companys_id

        response = self.client.post(reverse("demo_exit"))

        self.assertRedirects(response, reverse("index"))
        self.assertFalse(Companys.objects.filter(pk=demo_company_id).exists())
        self.assertTrue(Companys.objects.filter(pk=regular_company.pk).exists())

    def test_cleanup_removes_only_expired_demo_companies(self):
        self.client.post(reverse("demo_start"))
        demo_user = User.objects.get(pk=int(self.client.session["_auth_user_id"]))
        Companys.objects.filter(pk=demo_user.companys_id).update(
            demo_expires_at=timezone.now() - timedelta(minutes=1)
        )
        regular_company = Companys.objects.create(title="Рабочая компания")

        deleted = cleanup_expired_demo_companies()

        self.assertEqual(deleted, 1)
        self.assertFalse(Companys.objects.filter(pk=demo_user.companys_id).exists())
        self.assertTrue(Companys.objects.filter(pk=regular_company.pk).exists())

    def test_regular_authenticated_user_is_not_switched_to_demo(self):
        company = Companys.objects.create(title="Рабочая компания")
        user = User.objects.create_user(
            username="regular-demo-test",
            email="regular@example.test",
            password="test-pass-123",
            status="Администратор",
            companys=company,
        )
        self.client.force_login(user)

        response = self.client.post(reverse("demo_start"))

        self.assertRedirects(response, reverse("current_applications"), fetch_redirect_response=False)
        self.assertEqual(Companys.objects.filter(is_demo=True).count(), 0)

    @override_settings(DEMO_STARTS_PER_HOUR=1)
    def test_demo_creation_is_rate_limited_per_visitor(self):
        self.client.post(reverse("demo_start"), REMOTE_ADDR="192.0.2.20")
        self.client.logout()

        response = self.client.post(reverse("demo_start"), REMOTE_ADDR="192.0.2.20")

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Попробуйте снова через час", status_code=429)

    @override_settings(DEMO_MAX_ACTIVE_SESSIONS=0)
    def test_demo_creation_respects_global_capacity(self):
        response = self.client.post(reverse("demo_start"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(Companys.objects.filter(is_demo=True).count(), 0)

    def test_expired_session_is_logged_out_and_deleted(self):
        self.client.post(reverse("demo_start"))
        user = User.objects.get(pk=int(self.client.session["_auth_user_id"]))
        company_id = user.companys_id
        Companys.objects.filter(pk=company_id).update(
            demo_expires_at=timezone.now() - timedelta(seconds=1)
        )

        response = self.client.get(reverse("all_leads"))

        self.assertRedirects(response, reverse("demo_landing"), fetch_redirect_response=False)
        self.assertFalse(Companys.objects.filter(pk=company_id).exists())
        self.assertNotIn("_auth_user_id", self.client.session)
