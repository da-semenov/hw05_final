from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["group", "text", "image"]
        labels = {"group": "Группа", "text": "Текст", "image": "Изображение", }
        help_texts = {"group": "Выберите группу из списка",
                      "text": "Введите текст поста",
                      "image": "Добавьте картинку"}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {"text": "Комментарий"}
        help_texts = {"text": "Напишите здесь свой комментарий"}
