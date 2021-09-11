import http

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_author_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая информация',
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_urls_status_code(self):
        user_reader = User.objects.create(username='test_author_2')
        auth_client_reader = Client()
        auth_client_reader.force_login(user_reader)
        slug = PostsURLTests.group.slug
        pk = PostsURLTests.post.pk
        username = PostsURLTests.user.username
        url_client_status_code = (
            ('/', self.client, http.HTTPStatus.OK),
            ('/create/', self.auth_client, http.HTTPStatus.OK),
            (f'/group/{slug}/', self.client, http.HTTPStatus.OK),
            (f'/posts/{pk}/', self.client, http.HTTPStatus.OK),
            (f'/posts/{pk}/edit/', self.auth_client, http.HTTPStatus.OK),
            (f'/posts/{pk}/edit/', auth_client_reader, http.HTTPStatus.FOUND),
            (f'/profile/{username}/', self.client, http.HTTPStatus.OK),
            ('/no_page/', self.auth_client, http.HTTPStatus.NOT_FOUND),
            ('/no_page/', self.client, http.HTTPStatus.NOT_FOUND),
        )
        for (url, client, status_code) in url_client_status_code:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, status_code)

    def test_urls_redirect_correct(self):
        pk = PostsURLTests.post.pk
        reverse_edit = reverse('posts:post_edit', kwargs={'post_id': pk})
        reverse_login = reverse("login")
        reverse_create = reverse("posts:post_create")
        url_redirect_url = (
            (reverse('posts:post_create'),
             f'{reverse_login}?next={reverse_create}'),
            (reverse('posts:post_edit', kwargs={'post_id': pk}),
             f'{reverse_login}?next={reverse_edit}'),
        )
        for (url, redirect) in url_redirect_url:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect)
                self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_accordance_reverse_name_url(self):
        pk = PostsURLTests.post.pk
        username = PostsURLTests.post.author.username
        slug = PostsURLTests.group.slug
        reverse_name_url = (
            ('posts:index', None, '/'),
            ('posts:post_create', None, '/create/'),
            ('posts:group_list', {'slug': slug}, f'/group/{slug}/'),
            ('posts:post_edit', {'post_id': pk}, f'/posts/{pk}/edit/'),
            ('posts:post', {'post_id': pk}, f'/posts/{pk}/'),
            ('posts:profile', {'username': username}, f'/profile/{username}/')
        )
        for (name, args, url) in reverse_name_url:
            with self.subTest(url=url):
                self.assertEqual(reverse(name, kwargs=args), url)
