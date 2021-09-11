import os
import shutil

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User, Follow


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR,
                                           'temp_views_test'))
class PostsViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая информация',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def get_context_with_page_obj(self, reverse_name, kwargs=None):
        response = self.client.get(reverse(reverse_name, kwargs=kwargs))
        self.assertIn('page_obj', response.context)
        return response.context

    def test_view_correct_template(self):
        slug = PostsViewsTests.group.slug
        post_id = PostsViewsTests.post.pk
        username = PostsViewsTests.user.username
        reverse_name_template = (
            ('index', None, 'index.html'),
            ('group_list', {'slug': slug}, 'group_list.html'),
            ('profile', {'username': username}, 'profile.html'),
            ('post', {'post_id': post_id}, 'post_page.html'),
            ('post_edit', {'post_id': post_id}, 'update_post.html'),
            ('post_create', None, 'update_post.html'),
        )
        for (r_name, attr, template) in reverse_name_template:
            with self.subTest(r_name=r_name):
                response = self.auth_client.get(reverse(f'posts:{r_name}',
                                                        kwargs=attr))
                self.assertTemplateUsed(response, f'posts/{template}')

    def review_post(self, context, is_post=True):
        if is_post:
            self.assertIn('post', context)
            post = context['post']
        else:
            post = context['page_obj'][0]
        self.assertEqual(post.pk, PostsViewsTests.post.pk)
        self.assertEqual(post.group, PostsViewsTests.group)
        self.assertEqual(post.author, PostsViewsTests.user)
        self.assertEqual(post.text, PostsViewsTests.post.text)
        self.assertEqual(post.pub_date, PostsViewsTests.post.pub_date)

    def review_group(self, group):
        self.assertEqual(group.title, PostsViewsTests.group.title)
        self.assertEqual(group.slug, PostsViewsTests.group.slug)
        self.assertEqual(group.description, PostsViewsTests.group.description)
        self.assertEqual(group.pk, PostsViewsTests.group.pk)

    def test_home_page_show_correct_context(self):
        context = self.get_context_with_page_obj('posts:index')
        self.assertTrue(len(context['page_obj']) > 0)
        self.assertIsInstance(context['page_obj'][0], Post)
        self.review_post(context, is_post=False)

    def test_group_page_show_correct_context(self):
        slug = PostsViewsTests.group.slug
        context = self.get_context_with_page_obj('posts:group_list',
                                                 {'slug': slug})
        self.review_post(context, is_post=False)
        self.assertIn('group', context)
        self.review_group(context['group'])

    def test_profile_page_show_correct_context(self):
        name = PostsViewsTests.user.username
        context = self.get_context_with_page_obj('posts:profile',
                                                 {'username': name})
        self.assertIn('author', context)
        self.assertEqual(context['author'], PostsViewsTests.user)
        self.review_post(context, is_post=False)

    def test_post_detail_show_correct_context(self):
        pk = PostsViewsTests.post.pk
        response = self.client.get(reverse('posts:post',
                                           kwargs={'post_id': pk}))
        context = response.context
        self.review_post(context)

    def form_review(self, form):
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
            ('image', forms.fields.ImageField),
        )
        self.assertEqual(len(form.fields), len(form_fields))
        for (value, expected) in form_fields:
            with self.subTest(value=value):
                form_field = form.fields[value]
                self.assertIsInstance(form_field, expected)

    def review_post_on_page(self, posts, pk):
        self.assertEqual(posts[0].pk, pk)

    def test_create_post_show_correct_context(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.form_review(form)
        self.assertIsInstance(form, PostForm)

    def test_create_post_not_show_in_other_group(self):
        new_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='Тестовая информация и многое другое',
            group=PostsViewsTests.group,
        )
        slug2 = PostsViewsTests.group2.slug
        context = self.get_context_with_page_obj('posts:group_list',
                                                 {'slug': slug2})
        self.assertNotIn(new_post, context.get('page_obj'))

    def test_edit_post_show_correct_context(self):
        pk = PostsViewsTests.post.pk
        response = self.auth_client.get(reverse('posts:post_edit',
                                                kwargs={'post_id': pk}))
        self.assertIn('form', response.context)
        form = response.context['form']
        self.form_review(form)
        self.assertIsInstance(form, PostForm)

    def review_image_on_post(self, context, image, is_post=False):
        if is_post:
            self.assertIn('post', context)
            post = context['post']
        else:
            post = context['page_obj'][0]
        self.assertEqual(post.image, image)

    def test_show_post_image_on_page(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        upload_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_post = Post.objects.create(
            author=PostsViewsTests.user,
            text='new_text',
            group=PostsViewsTests.group,
            image=upload_image
        )
        reverse_name_args_key = (
            ('posts:group_list', {'slug': new_post.group.slug}),
            ('posts:profile', {'username': new_post.author.username}),
            ('posts:post', {'post_id': new_post.pk}),
            ('posts:index', None)
        )
        for name, kwargs in reverse_name_args_key:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                if name == 'posts:post':
                    self.review_image_on_post(response.context,
                                              new_post.image, is_post=True)
                else:
                    self.review_image_on_post(response.context, new_post.image)

    def get_content_by_reverse(self, revers_name, client=None):
        if not client:
            response = self.client.get(reverse(revers_name))
        else:
            response = client.get(reverse(revers_name))
        return response.content

    def test_index_page_cash(self):
        index_content = self.get_content_by_reverse('posts:index')
        _new_post = Post.objects.create(
            text='New_text',
            author=PostsViewsTests.user
        )
        content_index_page_cash = self.get_content_by_reverse('posts:index')
        self.assertEqual(index_content, content_index_page_cash)
        cache.clear()
        content_after_cache = self.get_content_by_reverse('posts:index',)
        self.assertNotEqual(index_content, content_after_cache)

    def create_new_auth_client(self):
        self.read_user = User.objects.create(username='user2')
        self.authorized_reader_client = Client()
        self.authorized_reader_client.force_login(self.read_user)

    def test_follow(self):
        count = self.user.following.count()
        self.create_new_auth_client()
        rev = reverse('posts:profile_follow',
                      kwargs={'username': self.user.username})
        self.authorized_reader_client.get(rev)
        follow = Follow.objects.filter(
            user=self.read_user,
            author=self.user).exists()
        self.assertEqual(count + 1, self.user.following.count())
        self.assertTrue(follow)

    def test_unfollow(self):
        self.create_new_auth_client()
        Follow.objects.create(user=self.read_user, author=self.user)
        count = self.user.following.count()
        username = self.user.username
        self.authorized_reader_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': username}))
        self.assertEqual(count - 1, self.user.following.count())

    def get_posts_on_page(self, reverse_name, client):
        response = client.get(reverse(reverse_name))
        self.assertIn('page_obj', response.context)
        return response.context['page_obj']

    def test_new_post_in_follow(self):
        self.create_new_auth_client()
        self.read_user2 = User.objects.create(username='user3')
        self.reader_client2 = Client()
        self.reader_client2.force_login(self.read_user2)

        Follow.objects.create(user=self.read_user, author=self.user)
        foll = self.authorized_reader_client
        not_foll = self.reader_client2
        new_post = Post.objects.create(
            text='Текст',
            author=self.user
        )
        cache.clear()

        posts_follow = self.get_posts_on_page(
            'posts:follow_index',
            foll
        )
        posts_not_follow = self.get_posts_on_page(
            'posts:follow_index',
            not_foll
        )
        self.assertIn(new_post, posts_follow)
        self.assertNotIn(new_post, posts_not_follow)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.num_posts = settings.NUMBER_OF_POSTS + 3
        block = Post(author=cls.user, group=cls.group, text='Тестовый текст')
        cls.post = Post.objects.bulk_create([block] * cls.num_posts)

    def test_first_page_contains_num_settings_records(self):
        response = self.client.get(reverse('posts:index'))
        length = len(response.context.get('page_obj').object_list)
        self.assertEqual(length, settings.NUMBER_OF_POSTS)

    def test_second_page_contains_last_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        length = len(response.context.get('page_obj').object_list)
        num_posts = PaginatorViewsTest.num_posts - settings.NUMBER_OF_POSTS
        self.assertEqual(length, num_posts)
