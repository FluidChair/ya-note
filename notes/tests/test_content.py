from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestInteractionNotes(TestCase):
    """
    Тестирование взаимодействия пользователей с заметками.

    Проверяет:
    - Отображение заметок в списке для разных пользователей
    - Наличие и корректность форм на страницах создания и редактирования
    - Права доступа к заметкам в зависимости от авторизации
    """
    @classmethod
    def setUpTestData(cls):
        """
        Создание тестовых данных перед выполнением всех тестов класса.

        Создаёт:
        - Автора заметки (User) - будет иметь доступ к своей заметке
        - Пользователя, не являющегося автором (User) - не должен видеть,
        чужую заметку
        - Заметку с заполненными полями (принадлежит автору)
        """
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_notes_list_for_different_users(self):
        """
        Проверка отображения заметок в списке для разных пользователей.

        Проверяет:
        - Автор заметки видит свою заметку в списке всех заметок
        - Не-автор не видит чужую заметку в своём списке
        """
        users_statuses = (
            (self.author, True),
            (self.not_author, False),
        )
        url = reverse('notes:list')
        for user, should_contain in users_statuses:
            with self.subTest(user=user, should_contain=should_contain):
                self.client.force_login(user)
                response = self.client.get(url)
                object_list = response.context['object_list']
                if should_contain:
                    self.assertIn(self.note, object_list)
                else:
                    self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        """
        Проверка наличия формы на страницах создания и редактирования заметок.

        Проверяет:
        1. Страница добавления заметки (notes:add) содержит форму
        2. Страница редактирования заметки (notes:edit) содержит форму
        3. Форма является экземпляром NoteForm
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug, ))
        )
        self.client.force_login(self.author)
        for name, args in urls:
            with self.subTest(page=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
