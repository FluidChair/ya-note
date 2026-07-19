from http import HTTPStatus

from notes.tests.base import BaseTestCase


class TestRoutes(BaseTestCase):
    """Тестирование маршрутов (URL-путей) приложения."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.NOTES_PAGES = (cls.detail_url, cls.edit_url, cls.delete_url)
        cls.USER_PAGES = (cls.list_url, cls.add_url, cls.success_url)
        cls.PUBLIC_PAGES = (cls.home_url, cls.login_url, cls.signup_url)

    def test_pages_status_codes_for_get_requests(self):
        """Проверка статус-кодов GET-запросов для различных пользователей."""
        test_cases = (
            # (client, urls, status)
            (
                self.client,
                self.PUBLIC_PAGES,
                HTTPStatus.OK
            ),
            (
                self.author_client,
                self.USER_PAGES + self.NOTES_PAGES,
                HTTPStatus.OK
            ),
            (
                self.not_author_client,
                self.NOTES_PAGES,
                HTTPStatus.NOT_FOUND
            ),
        )

        for client, urls, status in test_cases:
            for url in urls:
                with self.subTest(user=client, page=url, status=status):
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_logout_availability_for_anonymous_user(self):
        """Проверка доступности страницы выхода для анонимного пользователя."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirects_for_anonymous_user(self):
        """Проверка перенаправления анонимных пользователей на стр входа."""
        test_cases = self.NOTES_PAGES + self.USER_PAGES
        for url in test_cases:
            with self.subTest(page=url):
                response = self.client.get(url)
                expected_url = f'{self.login_url}?next={url}'
                self.assertRedirects(response, expected_url)
