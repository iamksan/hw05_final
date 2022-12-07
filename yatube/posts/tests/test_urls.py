from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestAuthor")
        cls.user_not_author = User.objects.create_user(
            username="TestNotAuthor"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая запись",
        )

        cls.templates_url_names_public = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug},
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.user.username},
            ),
        }
        cls.templates_url_names_private = {
            'posts/post_create.html': reverse('posts:post_create')
        }

        cls.templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug},
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.user.username},
            ),
            'posts/post_create.html': reverse('posts:post_create'),
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

        cache.clear()

    def test_guest_urls_access(self):
        """Страницы доступные любому пользователю."""
        for address in self.templates_url_names_public.values():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_autorized_urls_access(self):
        """Страницы доступные авторизованному пользователю."""
        for address in self.templates_url_names.values():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    # Проверяем редиректы для неавторизованного пользователя
    def test_list_url_redirect_guest(self):
        """Страницы перенаправляют анонимного пользователя
        на страницу логина.
        """
        for template, reverse_name in self.templates_url_names_private.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 302)
        response = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            )
        )
        self.assertEqual(response.status_code, 302)
    # Редирект для не автора

    def test_redirect_not_author(self):
        """Редирект при попытке редактирования поста не авром"""
        response = self.authorized_client_not_author.get(
            f"/posts/{self.post.pk}/edit/", follow=True
        )
        self.assertRedirects(response, f"/posts/{self.post.pk}/")
    # Страница не найденна

    def test_page_not_found(self):
        """Страница не найденна."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, 404)
