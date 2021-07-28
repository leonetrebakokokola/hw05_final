from django.test import TestCase, Client
from ..models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.userOne = User.objects.create_user(username='test-user')
        cls.userTwo = User.objects.create_user(username='test-user-2')
        cls.group = Group.objects.create(
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='test-post',
            author=cls.userOne,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.userOne)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(self.userTwo)

    def test_url_user_authorized(self):
        adress_url_names = {
            '/',
            '/group/test-slug/',
            '/test-user/',
            f'/test-user/{self.post.id}/'
        }
        # Проверка всех страниц - если пользователь авторизован
        for adress in adress_url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_new_post_url_not_authorized(self):
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/new/')

    def test_post_edit_url_not_authorized(self):
        response = self.guest_client.get(
            f'/test-user/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/test-user/{self.post.id}/edit/')

    def test_post_edit_url_authorized_author(self):
        response = self.authorized_client.get(
            f'/test-user/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_authorized_not_author(self):
        response = self.authorized_client_two.get(
            f'/test-user/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/test-user/{self.post.id}/')

    def test_url_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group.html',
            '/new/': 'posts/post_form.html',
            f'/test-user/{self.post.id}/edit/': 'posts/post_form.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

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
