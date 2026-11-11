from django.test import TestCase
from django.urls import reverse


class LandingPageTests(TestCase):
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
