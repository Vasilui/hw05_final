from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text_text_text_text_text_text'
        )

    def test_models_have_correct_name(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post),
                          'Неверное работает метод __str__ для модели Post')

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verbose = (
            ('text', 'Текст поста'),
            ('author', 'Автор'),
            ('group', 'Группа'),
        )
        for (value, expected) in field_verbose:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected)

    def test_help_text(self):
        field_help_texts = (
            ('group', 'Выберите группу'),
            ('text', 'Введите текст поста'),
        )
        for (value, expected) in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(value).help_text,
                    expected)


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_name(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group),
                          'Неверно работает метод __str__ для модели Group')

    def test_verbose_name(self):
        field_verbose = (
            ('title', 'Название'),
            ('slug', 'Слаг'),
            ('description', 'Описание'),
        )
        for (value, expected) in field_verbose:
            with self.subTest(value=value):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(value).verbose_name,
                    expected)

    def test_help_text(self):
        field_help_texts = (
            ('title', 'Введите название группы'),
            ('description', 'Введите описание группы'),
        )
        for (value, expected) in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(value).help_text,
                    expected)
