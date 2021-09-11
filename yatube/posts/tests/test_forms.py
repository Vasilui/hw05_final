import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def comment_post(client, author):
    new_post = Post.objects.create(
        text='text_text_text',
        author=PostFormTests.user
    )
    count_comments = new_post.comments.count()
    form_data = {'text': 'new_comments'}
    client.post(
        reverse('posts:add_comment', kwargs={'post_id': new_post.pk}),
        data=form_data,
        follow=True
    )
    return count_comments, new_post.comments.count()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
        )
        cls.group2 = Group.objects.create(
            title='test_group_2',
            slug='test_slug_2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_post_create_by_auth_user(self):
        count_post_before = Post.objects.count()
        form_data = {
            'text': 'new_text-new_text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, f'/profile/{post.author.username}/')
        self.assertEqual(Post.objects.count(), count_post_before + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostFormTests.group)
        self.assertEqual(post.author, PostFormTests.user)

    def test_post_create_by_no_auth_user(self):
        count_post_before = Post.objects.count()
        form_data = {
            'text': 'new_text',
            'group': self.group2.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        reverse_create = reverse('posts:post_create')
        reverse_login = reverse('login')
        self.assertRedirects(response,
                             f'{reverse_login}?next={reverse_create}')
        self.assertEqual(Post.objects.count(), count_post_before)

    def test_post_edit_author_by_post(self):
        new_post = Post.objects.create(
            author=PostFormTests.user,
            text='text-text-text',
            group=PostFormTests.group
        )
        form_data = {
            'text': 'new_text',
            'group': self.group2.id,
        }
        old_count = Post.objects.count
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': new_post.pk}),
            data=form_data, follow=True
        )
        new_post.refresh_from_db()
        self.assertEqual(Post.objects.count, old_count)
        self.assertRedirects(response, f'/posts/{new_post.pk}/')
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group, PostFormTests.group2)
        self.assertEqual(new_post.author, PostFormTests.user)

    def test_post_edit_auth_user_no_author(self):
        user_reader = User.objects.create(username='auth_user_2')
        authorized_client_reader = Client()
        authorized_client_reader.force_login(user_reader)
        new_post = Post.objects.create(
            author=PostFormTests.user,
            text='text-text-text',
            group=PostFormTests.group
        )
        form_data = {
            'text': 'new_text_text',
            'group': PostFormTests.group2.id,
        }
        old_count = Post.objects.count
        response = authorized_client_reader.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': new_post.pk}),
            data=form_data, follow=True
        )
        new_post.refresh_from_db()
        self.assertEqual(Post.objects.count, old_count)
        self.assertRedirects(response, f'/posts/{new_post.pk}/')
        self.assertNotEqual(new_post.text, form_data['text'])
        self.assertNotEqual(new_post.group, PostFormTests.group2)
        self.assertNotEqual(new_post.author, user_reader)

    def test_record_image_in_database(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'new_text_text',
            'image': uploaded,
        }
        post_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_post_comment_by_auth_user(self):
        auth_user = User.objects.create(username='auth_user')
        auth_client = Client()
        auth_client.force_login(auth_user)
        old_count, count = comment_post(auth_client, auth_user.username)
        self.assertEqual(count, old_count + 1)

    def test_post_comment_by_no_auth_user(self):
        old_count, count = comment_post(self.client, self.user.username)
        self.assertEqual(count, old_count)

    def test_exist_comment_after_comments(self):
        new_post = Post.objects.create(
            text='text_text_text',
            author=PostFormTests.user
        )
        form_data = {
            'text': 'new_comments',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': new_post.pk}),
            data=form_data,
            follow=True
        )
        new_post.refresh_from_db()
        comment = new_post.comments.all()[0]
        self.assertEqual(comment.author, PostFormTests.user)
        self.assertEqual(comment.post, new_post)
        self.assertEqual(comment.text, form_data['text'])
