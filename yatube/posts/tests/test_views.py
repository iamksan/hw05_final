from django.http import Http404
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import TestCase, Client
from django.conf import settings

from ..models import Post, Group, Comment, Follow

from django.urls import reverse
from django import forms
from django.core.cache import cache

TEST_OF_POST: int = 13
User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_2 = User.objects.create_user(username='test_user_2')
        cls.authorized_client = Client()
        cls.authorized_client_2 = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_2.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title='smt',
            slug='test_slug',
            description='random-group'
        )
        cls.image = ('posts/d60625a5fd7f47e21bd862554e0efbe0'
                     '--large-art-prints-cartoon-network.jpg')
        cls.number_of_created_posts = 13
        for _ in range(cls.number_of_created_posts):
            cls.post = Post.objects.create(
                text=('foo'),
                author=cls.user,
                group=cls.group,
                image=cls.image
            )
        cls.another_group = Group.objects.create(
            title='another_group',
            slug='new_slug',
            description='random-group_2'
        )
        cls.group_slug = cls.group.slug
        cls.post_id = cls.post.id
        cls.username = cls.user.username
        cls.index_url = (
            'posts:index',
            'posts/index.html',
            None
        )
        cls.group_list_url = (
            'posts:group_list',
            'posts/group_list.html',
            {'slug': cls.group_slug}
        )
        cls.profile_url = (
            'posts:profile',
            'posts/profile.html',
            {'username': cls.username}
        )
        cls.post_detail_url = (
            'posts:post_detail',
            'posts/post_detail.html',
            {'post_id': cls.post_id}
        )
        cls.post_comment_url = (
            'posts:add_comment',
            None,
            {'post_id': cls.post_id}
        )
        cls.post_edit_url = (
            'posts:post_edit',
            'posts/create_post.html',
            {'post_id': cls.post_id}
        )
        cls.post_create_url = (
            'posts:create',
            'posts/create_post.html',
            None
        )
        cls.index_follow = (
            'posts:follow_index',
            None,
            None
        )
        cls.profile_follow_url = (
            'posts:profile_follow',
            None,
            {'username': cls.user_2.username}
        )
        cls.profile_unfollow_url = (
            'posts:profile_unfollow',
            None,
            {'username': cls.user_2.username}
        )
        cls.pages_urls = (
            cls.index_url,
            cls.group_list_url,
            cls.profile_url,
            cls.post_detail_url,
            cls.post_edit_url,
            cls.post_create_url
        )
        cls.paginator_url = (
            cls.index_url,
            cls.group_list_url,
            cls.profile_url
        )
        cls.pages_with_post_images = (
            cls.index_url,
            cls.profile_url,
            cls.group_list_url,
        )
        cls.all_pks = [post.id for post in Post.objects.filter(
            image__isnull=False)
        ]

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

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
                form_field = response.context['form'].fields[value]
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


class PostsPagesTests(TestCase):
    @classmethod
    def test_are_post_with_group_exists_in_appropriate_pages(self):
        for address, _, args in PostsPagesTests.paginator_url:
            with self.subTest(address=address):
                response = PostsPagesTests.authorized_client.get(
                    reverse(address, kwargs=args)
                )
                for number_of_post in range(10):
                    self.assertIsNotNone(
                        response.context['page_obj'][number_of_post]
                    )
                response = PostsPagesTests.authorized_client.get(
                    reverse(address, kwargs=args) + '?page=2'
                )
                for number_of_post in range(3):
                    self.assertIsNotNone(
                        response.context['page_obj'][number_of_post]
                    )

    def test_image_in_pages_with_posts(self):
        for address, _, args in PostsPagesTests.pages_with_post_images:
            with self.subTest(address=address):
                response = PostsPagesTests.authorized_client.get(
                    reverse(address, kwargs=args)
                )
                for number_of_post in range(10):
                    post = response.context['page_obj'][number_of_post]
                    self.assertEqual(post.image, PostsPagesTests.image)
                response = PostsPagesTests.authorized_client.get(
                    reverse(address, kwargs=args) + '?page=2'
                )
                for number_of_post in range(3):
                    post = response.context['page_obj'][number_of_post]
                    self.assertEqual(post.image, PostsPagesTests.image)

    def test_post_detail_image(self):
        for pk in PostsPagesTests.all_pks:
            response = PostsPagesTests.authorized_client.get(
                reverse(
                    PostsPagesTests.post_detail_url[0],
                    kwargs={'post_id': pk}
                )
            )
            post_image = response.context['post'].image
            self.assertEqual(post_image, PostsPagesTests.image)

    def test_new_comment_is_created(self):
        form_data = {
            'text': 'test_text'
        }
        PostsPagesTests.authorized_client.post(
            reverse(
                PostsPagesTests.post_comment_url[0],
                kwargs=PostsPagesTests.post_comment_url[2]
            ),
            data=form_data,
            follow=True
        )
        try:
            new_comment = get_object_or_404(Comment, text='test_text')
        except Http404:
            new_comment = None
        self.assertIsNotNone(new_comment)

    def test_index_post_is_in_cache_after_deleting(self):
        response_1 = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_url[0])
        )
        content_before_post_deletion = response_1.content
        post_to_delete = Post.objects.get(pk=1)
        post_to_delete.delete()
        response_2 = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_url[0])
        )
        content_after_post_deletion = response_2.content
        self.assertEqual(
            content_before_post_deletion,
            content_after_post_deletion)

    def test_index_post_is_not_in_content_if_cache_cleared(self):
        response_1 = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_url[0])
        )
        content_before_post_deletion = response_1.content
        post_to_delete = Post.objects.get(pk=1)
        post_to_delete.delete()
        cache.clear()
        response_2 = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_url[0])
        )
        content_after_post_deletion = response_2.content
        self.assertNotEqual(
            content_before_post_deletion,
            content_after_post_deletion)

    def test_authorized_user_can_follow(self):
        author_username = PostsPagesTests.profile_follow_url[2]['username']
        author = User.objects.get(username=author_username)
        PostsPagesTests.authorized_client.get(
            reverse(
                PostsPagesTests.profile_follow_url[0],
                kwargs={'username': author_username})
        )
        following = Follow.objects.filter(
            author=author,
            user=PostsPagesTests.user
        ).exists()
        self.assertTrue(following)

    def test_authorized_user_can_unfollow(self):
        author_username = PostsPagesTests.profile_follow_url[2]['username']
        author = User.objects.get(username=author_username)
        PostsPagesTests.authorized_client.get(
            reverse(
                PostsPagesTests.profile_follow_url[0],
                kwargs={'username': author_username})
        )
        PostsPagesTests.authorized_client.get(
            reverse(
                PostsPagesTests.profile_unfollow_url[0],
                kwargs={'username': author_username})
        )
        following = Follow.objects.filter(
            author=author,
            user=PostsPagesTests.user
        ).exists()
        self.assertFalse(following)

    def test_new_posts_from_following_are_exists(self):
        author_username = PostsPagesTests.profile_follow_url[2]['username']
        author = User.objects.get(username=author_username)
        PostsPagesTests.authorized_client.get(
            reverse(
                PostsPagesTests.profile_follow_url[0],
                kwargs={'username': author_username})
        )
        response = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_follow[0])
        ).content
        Post.objects.create(
            text='fdfsfsdfsdfsdfsdffvdcvcx',
            author=author,
        )
        response_2 = PostsPagesTests.authorized_client.get(
            reverse(PostsPagesTests.index_follow[0])
        ).content
        self.assertNotEqual(response, response_2)

    def test_new_posts_from_following_are_exists(self):
        author_username = PostsPagesTests.profile_follow_url[2]['username']
        author = User.objects.get(username=author_username)
        response = PostsPagesTests.authorized_client_2.get(
            reverse(PostsPagesTests.index_url[0])
        ).content
        Post.objects.create(
            text='fdfsfsdfsdfsdfsdffvdcvcx',
            author=author,
        )
        response_2 = PostsPagesTests.authorized_client_2.get(
            reverse(PostsPagesTests.index_url[0])
        ).content
        self.assertEqual(response, response_2)
