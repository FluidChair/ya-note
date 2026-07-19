from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.base import BaseTestCase


class TestRightsNotes(BaseTestCase):
    """Тестирование прав доступа и операций с заметками."""

    FORM_DATA = {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }

    def test_user_can_create_note(self):
        """Проверка возможности создания заметки авторизованным пользователем."""
        Note.objects.all().delete()

        response = self.author_client.post(self.add_url, data=self.FORM_DATA)
        self.assertRedirects(response, self.success_url)

        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()

        self.assertEqual(new_note.title, self.FORM_DATA['title'])
        self.assertEqual(new_note.text, self.FORM_DATA['text'])
        self.assertEqual(new_note.slug, self.FORM_DATA['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Проверка запрета создания заметки анонимным пользователем."""
        initial_count = Note.objects.count()

        response = self.client.post(self.add_url, data=self.FORM_DATA)
        expected_url = f'{self.login_url}?next={self.add_url}'

        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_not_unique_slug(self):
        """Проверка валидации неуникального slug при создании заметки."""
        initial_count = Note.objects.count()

        data = self.FORM_DATA.copy()
        data['slug'] = self.note.slug
        response = self.author_client.post(self.add_url, data=data)

        self.assertEqual(Note.objects.count(), initial_count)
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.note.slug + WARNING)
        )

    def test_empty_slug(self):
        """Проверка автоматического создания slug из заголовка."""
        Note.objects.all().delete()

        data = self.FORM_DATA.copy()
        data.pop('slug')
        response = self.author_client.post(self.add_url, data=data)
        self.assertRedirects(response, self.success_url)

        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()

        expected_slug = slugify(self.FORM_DATA['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Проверка возможности редактирования заметки её автором."""
        response = self.author_client.post(self.edit_url, self.FORM_DATA)
        self.assertRedirects(response, self.success_url)

        update_note = Note.objects.get(id=self.note.id)
        self.assertEqual(update_note.title, self.FORM_DATA['title'])
        self.assertEqual(update_note.text, self.FORM_DATA['text'])
        self.assertEqual(update_note.slug, self.FORM_DATA['slug'])
        self.assertEqual(update_note.author, self.author)

    def test_author_can_delete_note(self):
        """Проверка возможности удаления заметки её автором."""
        initial_count = Note.objects.count()

        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), initial_count - 1)

    def test_other_user_cant_edit_note(self):
        """Проверка запрета редактирования заметки пользователем, не автором."""
        response = self.not_author_client.post(self.edit_url, self.FORM_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        update_note = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, update_note.title)
        self.assertEqual(self.note.text, update_note.text)
        self.assertEqual(self.note.slug, update_note.slug)
        self.assertEqual(self.note.author, update_note.author)

    def test_other_user_cant_delete_note(self):
        """Проверка запрета удаления заметки пользователем, не автором."""
        initial_count = Note.objects.count()

        response = self.not_author_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count)
