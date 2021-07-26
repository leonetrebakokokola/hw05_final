from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_author(self):
        adress_url_names = {
            reverse('about:author'),
            reverse('about:tech'),
        }
        # Проверка всех страниц - если пользователь авторизован
        for adress in adress_url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_about_page_template(self):
        templates_url_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
