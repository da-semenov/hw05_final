from django.core.cache import cache
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
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username="sarah")
        self.client.force_login(self.user)
        self.group = Group.objects.create(title="Тестовая", slug="test", description="Тестовая группа")

        with open("media/posts/test1.jpg", "rb") as img:
            self.client.post("/new/", {"text": "Тест", "group": self.group.id, "image": img})

    def test_image_index(self):
        """Тест картинки на главной странице"""
        response = self.client.get(reverse("index"))
        self.assertContains(response, "<img ", status_code=200)

    def test_image_profile(self):
        """Тест картинки на странице профиля автора"""
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertContains(response, "<img ", status_code=200)

    def test_image_post(self):
        """Тест картинки на странице конкретной записи"""
        response = self.client.get("/sarah/1/")
        self.assertContains(response, "<img ", status_code=200)

    def test_image_group_post(self):
        """Тест картинки на странице группы"""
        response = self.client.get("/group/test/")
        self.assertContains(response, "<img ", status_code=200)

    def test_image_upload(self):
        """Защита от загрузки файлов не-графических форматов"""
        with open("media/tester.txt", "rb") as img:
            response = self.client.post(
                "/new/", {"group": self.group.id, "text": "Test123", "image": img})
        self.assertNotContains(response, "<img ", status_code=200,
                               msg_prefix="Файл который вы загрузили не является изображением")


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
        self.link = Follow.objects.filter(user=self.follower, author=self.following)

    def test_follow(self):
        """Авторизованный пользователь может подписываться на других пользователей"""
        response = self.client.get(reverse("profile_follow", kwargs={
                                           "username": self.following}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.link.exists())
        self.assertEqual(1, Follow.objects.count())

    def test_unfollow(self):
        """Авторизованный пользователь может удалять из подписок других пользователей"""
        response = self.client.get(reverse("profile_unfollow", kwargs={
                                           "username": self.following}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.link.exists())
        self.assertEqual(0, Follow.objects.count())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан"""
        Follow.objects.create(user=self.follower, author=self.following)
        follow_index_url = reverse("follow_index")
        response = self.client.get(follow_index_url)
        self.assertContains(response, self.post.text)
        """Не появляется в ленте тех, кто не подписан на него"""
        self.client.force_login(self.user)
        response = self.client.get(follow_index_url)
        self.assertNotContains(response, self.post.text)
