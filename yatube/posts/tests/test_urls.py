# Все тесты из 5 спринта я удалил - чтоб не путаться
from django.test import TestCase, Client


class URLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_page_not_found(self):
        adress_url_names = {
            '/none/',
            '/404/',
            '/404/none/',
        }
        for adress in adress_url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 404)
