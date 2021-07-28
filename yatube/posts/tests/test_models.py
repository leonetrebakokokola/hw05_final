from django.test import TestCase
from ..models import Post, Group
from django.contrib.auth import get_user_model

User = get_user_model()


class ModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(title='test-group')
        cls.post = Post.objects.create(
            text='Текст - не более 15 символов',
            author=cls.user,
        )

    def test_str_post(self):
        post = ModelTests.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_str_group(self):
        group = ModelTests.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
