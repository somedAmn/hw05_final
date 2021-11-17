import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from yatube.settings import PAGINATOR_COUNT

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.another_author = User.objects.create_user(
            username='test-another_author'
        )
        cls.user = User.objects.create_user(username='test-user')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description'
        )
        cls.post_without_group = Post.objects.create(
            text='test-text_without_group',
            author=cls.author
        )
        cls.post_with_group = Post.objects.create(
            text='test-text_with_group',
            author=cls.author,
            group=cls.group
        )
        cls.post_another_author = Post.objects.create(
            text='test-text_another_author',
            author=cls.another_author
        )
        cls.post_with_image = Post.objects.create(
            text='test-text_with_image',
            author=cls.another_author,
            image=cls.uploaded,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='test-comment_text',
            author=cls.another_author,
            post=cls.post_with_image
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.another_author_client = Client()
        self.another_author_client.force_login(self.another_author)

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post_without_group.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post_without_group.pk}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]

        self.assertIn(
            first_object.text,
            [
                PostPagesTests.post_without_group.text,
                PostPagesTests.post_with_group.text,
                PostPagesTests.post_another_author.text,
                PostPagesTests.post_with_image.text
            ]
        )
        self.assertIn(
            first_object.author,
            [self.author, self.another_author]
        )
        if first_object.image:
            self.assertEqual(
                first_object.image,
                f'posts/{PostPagesTests.image_name}'
            )

    def test_follow_index_page_show_correct_context(self):
        follow_text = 'test-follow_text'
        Post.objects.create(
            text='123',
            author=self.user
        )
        Post.objects.create(
            text=follow_text,
            author=self.another_author
        )
        Follow.objects.create(
            user=self.author,
            author=self.another_author
        )
        Follow.objects.create(
            user=self.another_author,
            author=self.user
        )
        response = self.author_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]

        self.assertEqual(first_object.text, follow_text)
        self.assertEqual(first_object.author, self.another_author)

        response = self.another_author_client.get(
            reverse('posts:follow_index')
        )
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.text, follow_text)
        self.assertNotEqual(first_object.author, self.another_author)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': PostPagesTests.group.slug}
            )
        )

        group = response.context['group']
        first_object = response.context['page_obj'][0]

        if first_object.image:
            self.assertEqual(
                first_object.text, PostPagesTests.post_with_image.text
            )
            self.assertEqual(first_object.author, self.another_author)
            self.assertEqual(
                first_object.image,
                f'posts/{PostPagesTests.image_name}'
            )
        else:
            self.assertEqual(
                first_object.text, PostPagesTests.post_with_group.text
            )
            self.assertEqual(first_object.author, self.author)
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.another_author.username}
            )
        )
        first_object = response.context['page_obj'][0]
        profile = response.context['profile']
        post_count = response.context['post_count']
        another_author_post = Post.objects.filter(author=self.another_author)

        if first_object.image:
            self.assertEqual(
                first_object.text, PostPagesTests.post_with_image.text
            )
            self.assertEqual(
                first_object.image,
                f'posts/{PostPagesTests.image_name}'
            )
        else:
            self.assertEqual(
                first_object.text, PostPagesTests.post_another_author.text
            )
        self.assertEqual(profile, self.another_author)
        self.assertEqual(post_count, another_author_post.count())
        self.assertEqual(first_object.author, self.another_author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post_with_image.pk}
            )
        )
        post = response.context['post']
        profile = response.context['profile']
        first_comments = response.context['comments'][0]

        self.assertEqual(post, self.post_with_image)
        self.assertEqual(profile, self.another_author)
        self.assertEqual(first_comments, PostPagesTests.comment)
        self.assertEqual(
            post.image,
            f'posts/{PostPagesTests.image_name}'
        )

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post_without_group.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_cache_correct_work(self):
        cache_text = 'test-cache_text'
        post = Post.objects.create(
            text=cache_text,
            author=PostPagesTests.author
        )
        self.client.get(reverse('posts:index'))
        Post.objects.filter(pk=post.pk).delete()
        response = self.client.get(reverse('posts:index'))
        last_post = response.context['page_obj'][0]
        self.assertEqual(last_post.text, cache_text)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        last_post = response.context['page_obj'][0]
        self.assertNotEqual(last_post.text, cache_text)

    def test_follow_authorized_user(self):
        follows_before = Follow.objects.filter(user=self.author).count()
        self.author_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.another_author.username}
            )
        )
        follows_after = Follow.objects.filter(user=self.author).count()
        self.assertEqual(follows_after, follows_before + 1)

    def test_unfollow_authorized_user(self):
        Follow.objects.create(
            user=self.author,
            author=self.another_author
        )
        follows_before = Follow.objects.filter(user=self.author).count()
        self.author_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostPagesTests.another_author.username}
            )
        )
        follows_after = Follow.objects.filter(user=self.author).count()
        self.assertEqual(follows_after, follows_before - 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description'
        )
        for i in range(PAGINATOR_COUNT + 3):
            Post.objects.create(
                text=f'test-text{i}',
                author=cls.author,
                group=cls.group
            )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAGINATOR_COUNT)

    def test_index_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_first_page_contains_ten_records(self):
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            )
        )
        self.assertEqual(len(response.context['page_obj']), PAGINATOR_COUNT)

    def test_group_list_second_page_contains_three_records(self):
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.author.username}
            )
        )
        self.assertEqual(len(response.context['page_obj']), PAGINATOR_COUNT)

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.author.username}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
