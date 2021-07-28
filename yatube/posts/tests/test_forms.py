import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from posts.models import Post, Group
from yatube import settings


User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
# Проверка когда отправили пост - что всё успешно проходит с картинкой
class FormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='test-post',
            author=cls.user,
            group=cls.group,
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test-post',
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            Post.objects.filter(text='test-post').first().text,
            form_data['text']
        )
        self.assertEqual(
            Post.objects.filter(text='test-post').first().author,
            form_data['author']
        )
        self.assertEqual(
            Post.objects.filter(text='test-post').first().group.id,
            form_data['group']
        )
        self.assertTrue(
            Post.objects.filter(
                text='test-post',
                author=self.user,
                image='posts/small.gif',
            ).exists())

    def test_edit_post(self):
        uploaded = SimpleUploadedFile(
            name='small-2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data_edit = {
            'text': 'test-post-edit',
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }),
            data=form_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': 'test-user', 'post_id': self.post.id}))
        self.assertEqual(
            Post.objects.filter(text='test-post-edit').first().text,
            form_data_edit['text']
        )
        self.assertEqual(
            Post.objects.filter(text='test-post-edit').first().author,
            form_data_edit['author']
        )
        self.assertEqual(
            Post.objects.filter(text='test-post-edit').first().group.id,
            form_data_edit['group']
        )
        self.assertTrue(
            Post.objects.filter(
                text='test-post-edit',
                author=self.user,
                image='posts/small-2.gif',
            ).exists())
