"""Тестирование (unittest) логики проекта yanews."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()

COMMENT_TEXT: str = 'Текст комментария'


class TestCommentCreation(TestCase):
    """Тестирование комментариев."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаем новость:
        cls.new = News.objects.create(title='Заголовок', text='Текст')
        # Адрес страницы с новостью:
        cls.url = reverse('news:detail', args=(cls.new.pk,))
        # Создаём пользователя и клиента, логинимся в клиенте:
        cls.user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        # Данные для POST-запроса при создании комментария:
        cls.form_data = {'text': COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        """Анонимный пользователь не может отправлять комментарии."""
        # Фиксируем в переменной, количество комментариев до запроса:
        count_comment_before = Comment.objects.count()
        # POST запрос от анонимного клиента на добавление комментария:
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        # Проверяем, что редирект привёл к странице логина:
        self.assertRedirects(response, expected_url)
        # Получаем количество комментариев из БД после запроса:
        count_comment_after = Comment.objects.count()
        # Убеждаемся, что заметка не создана:
        self.assertEqual(count_comment_before, count_comment_after)

    def test_user_can_create_comment(self):
        """Авторизованный пользователь может отправлять комментарии."""
        # Фиксируем в переменной, количество комментариев до запроса:
        count_comment_before = Comment.objects.count()
        # POST запрос от авторизованного клиента на добавление комментария:
        response = self.user_client.post(self.url, data=self.form_data)
        # Адрес раздела с комментариями:
        url_to_comments = f'{self.url}#comments'
        # Проверяем, что редирект привёл к разделу с комментариями:
        self.assertRedirects(response, url_to_comments)
        # Получаем количество комментариев из БД после запроса:
        count_comment_after = Comment.objects.count()
        # Убеждаемся, что комментарий добавлен:
        self.assertNotEqual(count_comment_before, count_comment_after)
        # Получаем объект комментария из БД:
        comment = Comment.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(comment.text, self.form_data['text'])
        self.assertEqual(comment.news, self.new)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        """Проверка запрещенных слов в комментарии."""
        # Фиксируем в переменной, количество комментариев до запроса:
        count_comment_before = Comment.objects.count()
        # Подготавливаем форму для добавления комментария с запрещенным словом:
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        # POST запрос от авторизованного клиента на добавление комментария,
        # в форме добавлено слово исключение:
        response = self.user_client.post(self.url, data=bad_words_data)
        # Получаем форму из контекста:
        form = response.context['form']
        # Проверяем, есть ли в ответе ошибка формы:
        self.assertFormError(form=form, field='text', errors=WARNING)
        # Получаем количество комментариев из БД после запоса:
        count_comment_after = Comment.objects.count()
        # Убеждаемся, что комментарий не добавлен:
        self.assertEqual(count_comment_before, count_comment_after)


class TestCommentEditDelete(TestCase):
    """Тестирование редактирования и удаления комментариев."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаём новость в БД:
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        # Адрес новости:
        news_url = reverse('news:detail', args=(cls.news.id,))
        # Адрес раздела с комментариями:
        cls.url_to_comments = f'{news_url}#comments'
        # Создаём пользователя - автора комментария:
        cls.author = User.objects.create(username='Автор комментария')
        # Создаём клиент для пользователя-автора:
        cls.author_client = Client()
        # "Логиним" пользователя-автора в клиенте:
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя:
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём объект комментария:
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=COMMENT_TEXT
        )
        # URL для редактирования комментария:
        cls.edit_url = reverse('news:edit', args=(cls.comment.pk,))
        # URL для удаления комментария:
        cls.delete_url = reverse('news:delete', args=(cls.comment.pk,))
        # Формируем данные для POST-запроса для редактирования комментария:
        cls.form_data_edit = {'text': 'Обновлённый комментарий'}

    def test_author_can_delete_comment(self):
        """Автор может удалить свой комментарий."""
        # Фиксируем в переменной, количество комментариев до запроса:
        count_comment_before = Comment.objects.count()
        # От имени автора комментария отправляем DELETE-запрос на удаление:
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с комментариями:
        self.assertRedirects(response, self.url_to_comments)
        # Проверяем статус-код:
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Получаем количество комментариев из БД после запроса:
        count_comment_after = Comment.objects.count()
        # Убеждаемся, что комментарий удален:
        self.assertNotEqual(count_comment_before, count_comment_after)

    def test_user_cant_delete_comment_of_another_user(self):
        """Пользователь не может удалить комментарий другого автора."""
        # Фиксируем в переменной, количество комментариев до запроса:
        count_comment_before = Comment.objects.count()
        # DELETE запрос на удаление от пользователя-читателя:
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем количество комментариев из БД:
        count_comment_after = Comment.objects.count()
        # Убеждаемся, что комментарий не удален:
        self.assertEqual(count_comment_before, count_comment_after)

    def test_author_can_edit_comment(self):
        """Автор может редактировать свой комментарий."""
        # POST запрос на редактирование от имени автора комментария:
        response = self.author_client.post(self.edit_url,
                                           data=self.form_data_edit)
        # Проверяем, что редирект привёл к разделу с комментариями:
        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария:
        self.comment.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.comment.text, self.form_data_edit['text'])

    def test_user_cant_edit_comment_of_another_user(self):
        """Пользователь не может редактировать комментарий другого автора."""
        # POST запрос на редактирование от имени другого пользователя:
        response = self.reader_client.post(self.edit_url,
                                           data=self.form_data_edit)
        # Проверяем, что вернулась 404 ошибка:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария:
        self.comment.refresh_from_db()
        # Проверяем, что текст комментария не изменился:
        self.assertNotEqual(self.comment.text, self.form_data_edit['text'])
