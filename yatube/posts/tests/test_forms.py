import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description'
        )
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
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_create_authorized_user(self):
        form_data = {
            'text': 'test-create_text'
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_created_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(last_created_post.text, form_data['text'])
        self.assertEqual(last_created_post.author, self.author)

    def test_post_edit_author(self):
        form_data = {
            'text': 'test-update_text'
        }
        self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        updated_post = get_object_or_404(Post, pk=PostFormTests.post.pk)
        self.assertEqual(updated_post.text, form_data['text'])
        self.assertEqual(updated_post.author, self.author)

    def test_post_create_guest_user(self):
        form_data = {
            'text': 'test-guest_text'
        }
        count_before = Post.objects.count()
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        count_after = Post.objects.count()
        post = Post.objects.filter(text=form_data['text'])
        self.assertFalse(post.exists())
        self.assertEqual(count_before, count_after)

    def test_post_edit_guest_user(self):
        form_data = {
            'text': 'test-guest_update_text'
        }
        self.client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        post = get_object_or_404(Post, pk=PostFormTests.post.pk)
        self.assertNotEqual(post.text, form_data['text'])

    def test_post_with_group_create_authorized_user(self):
        form_data = {
            'text': 'test-create_text_with_group',
            'group': PostFormTests.group.pk
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_created_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(last_created_post.text, form_data['text'])
        self.assertEqual(last_created_post.author, self.author)
        self.assertEqual(last_created_post.group.pk, form_data['group'])

    def test_post_with_group_edit_author(self):
        form_data = {
            'text': 'test-update_text_with_group',
            'group': PostFormTests.group.pk
        }
        self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        updated_post = get_object_or_404(Post, pk=PostFormTests.post.pk)
        self.assertEqual(updated_post.text, form_data['text'])
        self.assertEqual(updated_post.author, self.author)
        self.assertEqual(updated_post.group.pk, form_data['group'])

    def test_post_with_image_сreate_authorized_user(self):
        form_data = {
            'text': 'test-create_text_with_image',
            'image': PostFormTests.uploaded
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_created_post = Post.objects.order_by('-pk')[0]
        self.assertEqual(last_created_post.text, form_data['text'])
        self.assertEqual(last_created_post.author, self.author)
        self.assertEqual(
            last_created_post.image,
            f'posts/{PostFormTests.image_name}'
        )


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests2(TestCase):
    """Сlass of conflicting tests"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
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
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
    # тесты на создание и редактирование поста с картинкой
    # никак не хотят работать в одном классе,
    # но если вызывать каждый отдельно, они работают, почему?

    def test_post_with_image_edit_author(self):
        form_data = {
            'text': 'test-update_text_with_image',
            'image': PostFormTests2.uploaded
        }
        self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests2.post.pk}
            ),
            data=form_data,
            follow=True
        )
        updated_post = get_object_or_404(Post, pk=PostFormTests2.post.pk)
        self.assertEqual(updated_post.text, form_data['text'])
        self.assertEqual(updated_post.author, self.author)
        self.assertEqual(
            updated_post.image,
            f'posts/{PostFormTests2.image_name}'
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_create_authorized_user(self):
        form_data = {
            'text': 'test-comment_create_text'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        last_created_comment = Comment.objects.order_by('-pk')[0]
        self.assertEqual(last_created_comment.text, form_data['text'])
        self.assertEqual(last_created_comment.author, self.user)

    def test_comment_create_guest_user(self):
        form_data = {
            'text': 'test-comment_guest_text'
        }
        count_before = Comment.objects.count()
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        count_after = Comment.objects.count()
        self.assertEqual(count_before, count_after)
