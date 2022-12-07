from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post

TEST_OF_POST: int = 13
User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Привет!',
            author=cls.user,
            group=cls.group,
            image=cls.image,
        )

        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'},
            )
        }

        cls.template_page_name = {
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            )
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_posts_pages_use_correct_template(self):
        """Проверка, использует ли адрес URL соответствующий шаблон."""
        for template, adress in self.templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_posts_context_index_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.
        Появляется ли пост, при создании на главной странице.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        last_post = response.context['page_obj'][0]
        self.posts_check_all_fields(last_post)
        self.assertEqual(last_post, self.post)

    def test_posts_context_group_list_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.
        Появляется ли пост, при создании на странице его группы.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            )
        )
        test_group = response.context['group']
        test_post = response.context['page_obj'][0]
        self.posts_check_all_fields(test_post)
        self.assertEqual(test_group, self.group)
        self.assertEqual(str(test_post), str(self.post))

    def test_posts_context_post_create_template(self):
        """
        Проверка, сформирован ли шаблон post_create с
        правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_post_edit_template(self):
        """
        Проверка, сформирован ли шаблон post_edit с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            )
        )
        form_fields = {'text': forms.fields.CharField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_profile_template(self):
        """
        Проверка, сформирован ли шаблон profile с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            )
        )
        profile = {'user': self.post.author}
        for value, expected in profile.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)
        test_page = response.context['page_obj'][0]
        self.posts_check_all_fields(test_page)
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_posts_context_post_detail_template(self):
        """
        Проверка, сформирован ли шаблон post_detail с
        правильным контекстом.
        """
        for reverse_name in self.template_page_name.values():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
        profile = {'post': self.post}
        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_posts_not_from_foreign_group(self):
        """
        Проверка, при указании группы поста, попадает
        ли он в другую группу.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.posts_check_all_fields(post)
        self.assertEqual(post.group, self.group)


class PostsPaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        bilk_post: list = []
        for i in range(TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=cls.group,
                                  author=cls.user))
        Post.objects.bulk_create(bilk_post)

    def test_posts_if_first_page_has_ten_records(self):
        """Проверка, содержит ли первая страница 10 записей."""
        response = self.authorized_client.get(reverse('posts:index'))
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, settings.FIRST_OF_POSTS)

    def gen_natural_numbers():
        cur = 2
        while True:
            yield cur
            cur += 1
    natural_num_gen = gen_natural_numbers()

    def test_posts_if_second_page_has_three_records(self):
        """Проверка, содержит ли вторая страница 3 записи."""
        response = self.authorized_client.get(
            reverse('posts:index') + f'?page={next(self.natural_num_gen)}'
        )
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, TEST_OF_POST % settings.FIRST_OF_POSTS)
