from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class PostsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah")
        self.post = Post.objects.create(text="Test SkyNet!", author=self.user)

    def test_profile(self):
        """ После регистрации пользователя создается его персональная страница (profile) """
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertEqual(response.status_code, 200, "Профиль не существует")
        self.assertEqual(len(response.context["page"]), 1, "Новый пост не отображается на странице профиля")
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(response.context["author"].username, self.user.username, "Неверный профиль")

    def test_add_post_auth(self):
        """ Авторизованный пользователь может опубликовать пост (new) """
        self.client.force_login(self.user)
        response = self.client.get(reverse("new_post"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)

    def test_add_post_anonymous(self):
        """ Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа) """
        self.client.logout()
        response = self.client.get(reverse("new_post"))
        self.assertRedirects(response,
                             "/auth/login/?next=/new/",
                             msg_prefix="Анонимный пользователь не перенаправляется на страницу входа в систему")

    def test_post_home(self):
        """ После публикации поста новая запись появляется на главной странице сайта (index) """
        cache.clear()
        response = self.client.get(reverse("index"))
        self.assertIn(self.post,
                      response.context["page"],
                      "Новый пост должен появиться на главной странице сайта")
        self.assertEqual(self.post,
                         response.context["page"][0],
                         "Пост находящийся на главной странице неверен")

    def test_post_profile(self):
        """ Пост должен появиться на персональной странице пользователя (profile) """
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertIn(self.post,
                      response.context["page"],
                      "Новый пост должен появиться на странице профиля автора")
        self.assertEqual(self.post,
                         response.context["page"][0],
                         "Пост находищийся на странице профиля автора неверен")

    def test_post_view(self):
        """ Пост должен появиться на отдельной странице поста (post) """
        response = self.client.get(reverse("post", args=[self.user.username, self.post.id]))
        self.assertEqual(response.status_code, 200, "Отдельная страница поста не существует")
        self.assertEqual(self.post, response.context["post"],
                         "Пост должен появиться на отдельной странице просмотра записей")

    def test_edit_post_wrong_user(self):
        self.user = User.objects.create_user(username="john")
        self.post = Post.objects.create(text="Test", author=self.user)
        self.client.logout()
        self.user = User.objects.create_user(username="terminator")
        self.client.force_login(self.user)
        response = self.client.get(reverse("post_edit", args=["john", self.post.id]))
        self.assertRedirects(response,
                             reverse("post", args=["john", self.post.id]),
                             msg_prefix="Неверный пользователь не перенаправляется на страницу просмотра поста")

    def test_edit_post_auth(self):
        self.user = User.objects.create_user(username="john")
        self.post = Post.objects.create(text="Test", author=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("post_edit", args=[self.user.username, self.post.id]))
        self.assertEqual(response.status_code, 200,
                         "Авторизованный пользователь должен иметь возможность редактировать свои посты")
        """ Отредактированный пост должен обновиться на главной, в профиле автора и на отдельной странице """
        for url in (reverse("index"), reverse("profile", args=[self.user.username]),
                    reverse("post", args=[self.user.username, self.post.id])):
            response = self.client.get(url)
            self.assertContains(response,
                                self.post.text,
                                msg_prefix=f"Обновления не были отражены в {url}")

    def test_404(self):
        """ Возвращает ли сервер код 404, если страница не найдена """
        response = self.client.get("/404/")
        self.assertEquals(response.status_code, 404)


class ImageTest(TestCase):
    """Тесты картинок"""
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="sarah")
        self.client.force_login(self.user)
        self.group = Group.objects.create(title="Тестовая", slug="test", description="Тестовая группа")

    def test_post_with_image(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(name="some.gif",
                                 content=small_gif,
                                 content_type="image/gif",)
        post = Post.objects.create(author=self.user,
                                   text="text",
                                   group=self.group,
                                   image=img,)

        urls = [
            reverse("index"),
            reverse("profile", args=[self.user.username]),
            reverse("post", args=[self.user.username, post.id]),
            reverse("groups", args=[self.group.slug]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "<img")
                cache.clear()

    def test_upload_not_an_image(self):
        """Защита от загрузки файлов не-графических форматов"""
        not_image = SimpleUploadedFile(name="some.txt",
                                       content=b"abc",
                                       content_type="text/plain",)

        url = reverse("new_post")
        response = self.client.post(
            url, {"text": "some_text", "image": not_image},)

        self.assertFormError(response,
                             "form",
                             "image",
                             errors=("Загрузите правильное изображение. "
                                     "Файл, который вы загрузили, поврежден "
                                     "или не является изображением."
                                     ),
                             )


class CacheTest(TestCase):
    """Тест кэша"""
    def setUp(self):
        self.first_client = Client()
        self.second_client = Client()
        self.user = User.objects.create_user(username="sarah",)
        self.first_client.force_login(self.user)

    def cache_test(self):
        self.second_client.get(reverse("index"))
        self.first_client.post(reverse("new_post"), {"text": "Тест кэша"})
        response = self.second_client.get(reverse("index"))
        self.assertNotContains(response, "Тест кэша")
        cache.clear()
        response_cache_clear = self.second_client.get(reverse("index"))
        self.assertContains(response_cache_clear, "Тест кэша")


class CommentsTest(TestCase):
    """Тесты комментариев"""
    def setUp(self):
        self.auth_client = Client()
        self.client = Client()
        self.user = User.objects.create_user(username="terminator")
        self.post = Post.objects.create(author=self.user, text="SkyNet")
        self.auth_client.force_login(self.user)

    def test_comment(self):
        """Только авторизированный пользователь может комментировать посты"""
        comment_url = reverse("add_comment", kwargs={"username": self.user,
                                                     "post_id": self.post.id})
        self.auth_client.post(comment_url, {"text": "SkyNet"},
                              follow=True)

        comment = Comment.objects.filter(text="SkyNet").exists()
        response = self.auth_client.get(comment_url, follow=True)
        self.assertContains(response, "SkyNet")
        self.assertTrue(comment)

    def test_non_auth_comment(self):
        """Неавторизированный пользователь не может комментировать посты."""
        comment_url = reverse("add_comment", kwargs={"username": self.user,
                                                     "post_id": self.post.id})
        self.client.post(comment_url, {"text": "Test nonauth comment"}, follow=True)
        self.assertEqual(0, Comment.objects.filter(text="Test nonauth comment").count())


class FollowTest(TestCase):
    """Тесты подписок"""
    def setUp(self):
        self.client = Client()
        self.following = User.objects.create_user(username="sarah")
        self.follower = User.objects.create_user(username="terminator")
        self.user = User.objects.create_user(username="john")
        self.post = Post.objects.create(author=self.following, text="test SkyNET")
        self.client.force_login(self.follower)
        self.link_query = Follow.objects.filter(user=self.follower, author=self.following)

    def test_follow(self):
        """Авторизованный пользователь может подписываться на других пользователей"""
        response = self.client.get(reverse("profile_follow", kwargs={
                                           "username": self.following}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.link_query.exists())
        self.assertEqual(1, Follow.objects.count())

    def test_unfollow(self):
        """Авторизованный пользователь может удалять из подписок других пользователей"""
        response = self.client.get(reverse("profile_unfollow", kwargs={
                                           "username": self.following}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.link_query.exists())
        self.assertEqual(0, Follow.objects.count())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан"""
        Follow.objects.create(user=self.follower, author=self.following)
        follow_index_url = reverse("follow_index")
        response = self.client.get(follow_index_url)
        self.assertContains(response, self.post.text)

    def test_unfollow_index(self):
        """Не появляется в ленте тех, кто не подписан на него"""
        Follow.objects.create(user=self.follower, author=self.following)
        follow_index_url = reverse("follow_index")
        self.client.force_login(self.user)
        response = self.client.get(follow_index_url)
        self.assertNotContains(response, self.post.text)
