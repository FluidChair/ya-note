from notes.forms import NoteForm
from notes.tests.base import BaseTestCase


class TestInteractionNotes(BaseTestCase):
    """Тестирование взаимодействия пользователей с заметками."""

    def test_notes_list_for_different_users(self):
        """Проверка отображения заметок в списке для разных пользователей."""
        test_cases = (
            (self.author_client, self.assertIn),
            (self.not_author_client, self.assertNotIn),
        )
        for client, assertion in test_cases:
            with self.subTest(user=client):
                response = client.get(self.list_url)
                object_list = response.context['object_list']
                assertion(self.note, object_list)

    def test_pages_contains_form(self):
        """На страницах создания и редактирования есть форма."""
        test_cases = (self.add_url, self.edit_url)
        for url in test_cases:
            with self.subTest(page=url):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
