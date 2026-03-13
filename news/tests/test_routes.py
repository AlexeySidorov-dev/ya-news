"""Тестирование (unittest) маршрутов проекта yanews."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import Comment, News

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):
    """Тесты проекта ya-news."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаем новость:
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        # От имени автора создаём комментарий к новости:
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='Текст комментария'
        )

    def test_pages_availability(self):
        """Доступность страниц для анонимного пользователя."""
        urls = (
            ('news:home', None),
            ('news:detail', (self.news.pk,)),
            ('users:login', None),
            ('users:signup', None),
            ('users:logout', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                # Формируем URL:
                url = reverse(name, args=args)
                # Запрос от имени анонимного пользователя на
                # сформированную страницу:
                if name == 'users:logout':
                    response = self.client.post(url)  # POST запрос.
                else:
                    response = self.client.get(url)  # GET запрос.
                # Проверяем статус-код:
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_comment_edit_and_delete(self):
        """Доступность страниц по правам пользователя."""
        users_statuses = (
            # Автор комментария должен получить ответ OK:
            (self.author, HTTPStatus.OK),
            # Читатель должен получить ответ NOT_FOUND:
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('news:edit', 'news:delete'):
                with self.subTest(user=user, name=name):
                    # Формируем URL:
                    url = reverse(name, args=(self.comment.pk,))
                    # GET запрос от имени пользователя на сформированную
                    # страницу:
                    response = self.client.get(url)
                    # Проверяем статус-код:
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Редирект для анонимного пользователя."""
        # Сохраняем адрес страницы логина (перенаправление на нее):
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('news:edit', 'news:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.comment.pk,))  # Формируем URL.
                redirect_url = f'{login_url}?next={url}'  # Страница редиректа.
                # GET запрос от анонимного пользователя на сформированную
                # страницу:
                response = self.client.get(url)
                # Проверяем редирект:
                self.assertRedirects(response, redirect_url)
