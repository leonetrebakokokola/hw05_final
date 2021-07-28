import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Follow
from django import forms


User = get_user_model()


MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ViewTests(TestCase):
    # Проверка, что изображение передаётся в context
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.userTwo = User.objects.create_user(username='test-user-2')
        cls.userThree = User.objects.create_user(username='test-user-3')
        cls.group = Group.objects.create(slug='test-slug')
        cls.groupTwo = Group.objects.create(slug='test-slug-2')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test-post',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        Follow.objects.create(
            user=cls.userTwo,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_two = Client()
        self.authorized_client_two.force_login(self.userTwo)
        self.authorized_client_three = Client()
        self.authorized_client_three.force_login(self.userThree)

    def test_pages_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': self.group.slug})
            ),
            'posts/post_form.html': reverse('new_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        first_post = response.context['page'][0]
        self.assertEqual(first_post.text, 'test-post')
        self.assertEqual(first_post.image, 'posts/small.gif')

    def test_group_context(self):
        response = self.authorized_client.get(reverse(
            'group_posts',
            kwargs={'slug': self.group.slug}))
        first_post = response.context['page'][0]
        self.assertEqual(first_post.text, 'test-post')
        self.assertEqual(first_post.image, 'posts/small.gif')
        self.assertEqual(response.context['group'].slug, 'test-slug')

    def test_new_post_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {'text': forms.fields.CharField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        response = self.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            )
        )
        form_fields = {'text': forms.fields.CharField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_user_profile_context(self):
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        first_post = response.context['page'][0]
        self.assertEqual(first_post.text, 'test-post')
        self.assertEqual(first_post.image, 'posts/small.gif')

    def test_post_context(self):
        response = self.authorized_client.get(
            reverse(
                'post',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }))
        post = response.context['post']
        self.assertEqual(post.text, 'test-post')
        self.assertEqual(post.image, 'posts/small.gif')

    # Тест подписки и отписки
    def test_subscription(self):
        response = self.authorized_client.get(
            reverse(
                'profile_follow',
                kwargs={'username': self.userTwo.username}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Follow.objects.all().count(), 2)

    def test_unsubscribe(self):
        response = self.authorized_client.get(
            reverse(
                'profile_unfollow',
                kwargs={'username': self.userTwo.username}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Follow.objects.all().count(), 1)

    # Проверка есть ли пост на главной и на страницы группы
    def test_post_on_correct_index_and_group_page(self):
        pages_names = {
            reverse('index'),
            reverse('group_posts', kwargs={'slug': self.groupTwo.slug})
        }
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                for post in response.context.get('page').object_list:
                    self.assertEqual(post.text, 'test-post')

    # Проверка чтоб пост не был на не нужной страницы группы
    def test_post_not_another_group_page(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': self.groupTwo.slug}))
        self.assertEqual(len(response.context.get('page')), 0)

    # Проверка есть ли пост на нужной странице - избранных авторов
    def test_post_on_correct_follow_page(self):
        response = self.authorized_client_two.get(
            reverse('follow_index'))
        for post in response.context.get('page').object_list:
            self.assertEqual(post.text, 'test-post')

    # Проверка поста нету на не нужной странице - избранных авторов
    def test_post_not_another_follow_page(self):
        response = self.authorized_client_three.get(
            reverse('follow_index'))
        self.assertEqual(len(response.context.get('page')), 0)


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(slug='test-slug')

        for x in range(13):
            Post.objects.create(
                text=f'test-post-{x}',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_first_page(self):
        cache.clear()
        pages_names = {
            reverse('index'),
            reverse('group_posts', kwargs={'slug': self.group.slug}),
            reverse('profile', kwargs={'username': self.user.username}),
        }
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(len(response.context.get('page')), 10)

    def test_paginator_second_page(self):
        pages_names = {
            reverse('index'),
            reverse('group_posts', kwargs={'slug': self.group.slug}),
            reverse('profile', kwargs={'username': self.user.username}),
        }
        for adress in pages_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress + '?page=2')
                self.assertEqual(len(response.context.get('page')), 3)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_cache(self):
        Post.objects.create(
            text='test-post',
            author=self.user
        )
        response1 = self.authorized_client.get(reverse('index'))
        self.assertEqual(response1.context, None)

        cache.clear()

        response2 = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response2.context, None)
        self.assertEqual(response2.context['page'][0].text, 'test-post')
