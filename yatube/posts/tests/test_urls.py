from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_urls_status_code(self):
        urls = ['/', '/about/author/', '/about/tech/']

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.user = User.objects.create_user(username='test-user')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author
        )
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_unexisting_url_at_desired_location(self):
        """Несуществующая страница выдаёт ошибку 404."""
        response = self.client.get('unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_posts_url_exists_at_desired_location_for_guest_user(self):
        urls = [
            '/', f'/group/{PostURLTests.group.slug}/',
            f'/profile/{PostURLTests.user.username}/',
            f'/posts/{PostURLTests.post.pk}/'
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location_for_authorized_user(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location_for_author_user(self):
        response = self.author_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/', follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_redirect_anonymous_on_auth_login(self):
        url_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{PostURLTests.post.pk}/edit/':
                f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/'
        }
        for url, redirect in url_redirect.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect)

    def test_post_edit_url_redirect_no_author_on_post_detail(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит не автора
        на подробное описание поста.
        """
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.pk}/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.pk}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.author_client.get(adress)
                self.assertTemplateUsed(response, template)
