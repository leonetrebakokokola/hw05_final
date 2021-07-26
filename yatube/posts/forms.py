from django.forms import ModelForm
from django.forms import Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': ('Группа'),
            'text': ('Текст'),
            'image': ('Изображение')
        }
        help_texts = {
            'group': ('Группа для этой записи'),
            'text': ('Текст этой записи'),
            'image': ('Изображение для этой записи')
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 8})
        }
        labels = {
            'text': ('Текст'),
        }
        help_texts = {
            'text': ('Текст этого комментария'),
        }
