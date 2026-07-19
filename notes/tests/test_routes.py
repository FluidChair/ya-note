from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """
    Тестирование маршрутов (URL-путей) приложения.

    Проверяет доступность страниц для разных категорий пользователей:
    - Авторизованные пользователи
    - Анонимные пользователи
    - Автор заметки
    - Не автор заметки
    """
    NOTES_PAGES = ('notes:detail', 'notes:edit', 'notes:delete')
    USER_PAGES = ('notes:list', 'notes:add', 'notes:success')
    PUBLIC_PAGES = ('notes:home', 'users:login', 'users:signup')

    @classmethod
    def setUpTestData(cls):
        """
        Создание тестовых данных перед выполнением всех тестов класса.

        Создаёт:
        - Автора заметки (User)
        - Пользователя, не являющегося автором (User)
        - Заметку с заполненными полями
        """
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author = User.objects.create(username='Не автор')
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_availability_for_authorized_users(self):
        """
        Проверка доступности страниц для авторизованных пользователей.

        Проверяет:
        1. Страницы заметок (detail, edit, delete) доступны автору
        2. Страницы пользователя (list, add, success) доступны
        любому авторизованному пользователю
        """
        for name in self.NOTES_PAGES:
            with self.subTest(user='author', page=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        for name in self.USER_PAGES:
            with self.subTest(user='not_author', page=name):
                url = reverse(name)
                response = self.not_author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_anonymous_user(self):
        """
        Проверка доступности публичных страниц для анонимных пользователей.

        Проверяет, что домашняя страница, страницы входа и регистрации
        доступны без авторизации (статус 200 OK).
        """
        for name in self.PUBLIC_PAGES:
            with self.subTest(page=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_availability_for_anonymous_user(self):
        """
        Проверка доступности страницы выхода для анонимного пользователя.

        Проверяет, что анонимный пользователь может выполнить POST-запрос
        на выход из системы и получает статус 200 OK.
        """
        url = reverse('users:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Проверка доступности страниц заметок для разных пользователей.

        Проверяет:
        - Автор заметки имеет доступ к своим заметкам (статус 200 OK)
        - Не автор получает ошибку 404 Not Found при попытке доступа,
        к чужим заметкам
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in self.NOTES_PAGES:
                with self.subTest(user=user, page=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirects(self):
        """
        Проверка перенаправления анонимных пользователей на страницу входа.

        Проверяет, что все защищённые страницы (заметок и пользовательские)
        перенаправляют анонимного пользователя на страницу входа с параметром
        next, указывающим на запрашиваемую страницу.
        """
        urls = (
            *[(name, (self.note.slug,)) for name in self.NOTES_PAGES],
            *[(name, None) for name in self.USER_PAGES],
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(page=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                expected_url = f'{login_url}?next={url}'
                self.assertRedirects(response, expected_url)
