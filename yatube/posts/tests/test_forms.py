from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.user = User.objects.create_user(username="user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая запись",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        post_count = Post.objects.count()
        form_data = {
            "text": "Тестовая запись чезез форму",
            "group": self.group.pk,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""

        post_count = Post.objects.count()
        form_data = {
            "text": "Отредактированная запись.",
            "group": self.group.pk,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": str(self.post.pk)}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail", kwargs={"post_id": str(self.post.pk)}
            ),
        )
        # Проверяем, что не создался новый пост
        self.assertEqual(Post.objects.count(), post_count)
        post_edit = Post.objects.get(id=self.post.pk)
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(post_edit.group, self.group)

    def test_guest_new_post(self):
        # неавторизоанный не может создавать посты
        form_data = {
            'text': 'Пост от неавторизованного пользователя',
            'group': self.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertFalse(Post.objects.filter(
            text='Пост от неавторизованного пользователя').exists())
        self.assertRedirects(response, redirect)
