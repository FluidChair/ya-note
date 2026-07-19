from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestRightsNotes(TestCase):
    """
    Тестирование прав доступа и операций с заметками.

    Проверяет:
    - Создание заметок авторизованными и анонимными пользователями
    - Валидацию уникальности slug и автоматическое создание slug
    - Редактирование и удаление заметок автором и другими пользователями
    - Корректное перенаправление после операций
    """
    FORM_DATA = {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных, перед выполнением всех тестов класса."""
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

        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.redirect = reverse('notes:success')

    def test_user_can_create_note(self):
        """
        Проверка возможности создания заметки авторизованным пользователем.

        Проверяет:
        - После отправки формы происходит перенаправление на страницу success
        - В базе данных создаётся новая заметка (количество увеличивается на 1)
        - Все поля новой заметки соответствуют отправленным данным
        - Автор заметки правильно привязывается к текущему пользователю
        """
        response = self.author_client.post(
            reverse('notes:add'),
            data=self.FORM_DATA
        )
        self.assertRedirects(response, self.redirect)

        note_from_db = Note.objects.exclude(pk=self.note.pk)
        self.assertEqual(note_from_db.count(), 1)

        new_note = note_from_db.get()
        self.assertEqual(new_note.title, self.FORM_DATA['title'])
        self.assertEqual(new_note.text, self.FORM_DATA['text'])
        self.assertEqual(new_note.slug, self.FORM_DATA['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """
        Проверка запрета создания заметки анонимным пользователем.

        Проверяет:
        - Анонимный пользователь перенаправляется на страницу входа
        - В URL перенаправления присутствует параметр next с исходным адресом
        - Новая заметка не создаётся в базе данных
        """
        url = reverse('notes:add')
        response = self.client.post(url, data=self.FORM_DATA)
        expected_url = f'{reverse('users:login')}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """
        Проверка валидации неуникального slug при создании заметки.

        Проверяет:
        - При попытке создать заметку с уже существующим slug возникает ошибка
        - Ошибка привязана к полю 'slug'
        - Сообщение об ошибке содержит предупреждение о неуникальности
        - Новая заметка не создаётся в базе данных
        """
        data = self.FORM_DATA.copy()
        data['slug'] = self.note.slug
        response = self.author_client.post(
            reverse('notes:add'),
            data=data
        )
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """
        Проверка автоматического создания slug из заголовка.

        Проверяет:
        - При отправке формы без поля slug происходит перенаправление
        - Новая заметка создаётся в базе данных
        - Slug автоматически генерируется из заголовка с помощью slugify
        """
        data = self.FORM_DATA.copy()
        data.pop('slug')

        response = self.author_client.post(
            reverse('notes:add'),
            data=data
        )
        self.assertRedirects(response, self.redirect)
        note_from_db = Note.objects.exclude(pk=self.note.pk)
        self.assertEqual(note_from_db.count(), 1)

        note_from_db = note_from_db.get()
        expected_slug = slugify(self.FORM_DATA['title'])
        self.assertEqual(note_from_db.slug, expected_slug)

    def test_author_can_edit_note(self):
        """
        Проверка возможности редактирования заметки её автором.

        Проверяет:
        - После отправки формы редактирования происходит перенаправление
        - Данные заметки в базе данных обновляются на новые значения
        - Все поля (title, text, slug) соответствуют отправленным данным
        """
        response = self.author_client.post(self.edit_url, self.FORM_DATA)
        self.assertRedirects(response, self.redirect)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.FORM_DATA['title'])
        self.assertEqual(self.note.text, self.FORM_DATA['text'])
        self.assertEqual(self.note.slug, self.FORM_DATA['slug'])

    def test_author_can_delete_note(self):
        """
        Проверка возможности удаления заметки её автором.

        Проверяет:
        - После отправки DELETE-запроса происходит перенаправление
        - Заметка удаляется из базы данных (количество заметок становится 0)
        """
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.redirect)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_edit_note(self):
        """
        Проверка запрета редактирования заметки пользователем, не автором.

        Проверяет:
        - Не-автор получает статус 404 Not Found при попытке редактирования
        - Данные заметки в базе данных остаются неизменными
        - Все поля (title, text, slug) сохраняют исходные значения
        """
        response = self.not_author_client.post(self.edit_url, self.FORM_DATA)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get()
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_other_user_cant_delete_note(self):
        """
        Проверка запрета удаления заметки пользователем, не автором.

        Проверяет:
        - Не-автор получает статус 404 Not Found при попытке удаления
        - Заметка остаётся в базе данных (количество заметок не меняется)
        """
        response = self.not_author_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
