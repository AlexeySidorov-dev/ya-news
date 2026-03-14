"""Тестирование (unittest) контента проекта yanews."""

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News

User = get_user_model()


class TestHomePage(TestCase):
    """Тестирование главной страницы."""

    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Вычисляем текущую дату:
        today = datetime.today()
        all_news = [  # Создаем 11 новостей.
            News(title=f'Новость {index}',
                 text='Просто текст.',
                 # Для каждой новости уменьшаем дату на index дней от today,
                 # где index - счётчик цикла.
                 date=today - timedelta(days=index)
                 )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
        News.objects.bulk_create(all_news)

    def setUp(self):
        """Подготовка объектов."""
        # GET запрос от анонимного пользователя на главную страницу:
        self.response = self.client.get(self.HOME_URL)
        # Получаем список объектов из словаря контекста:
        self.object_list = self.response.context['object_list']

    def test_news_count(self):
        """Количество новостей на главной странице."""
        # Определяем количество новостей в списке:
        news_count = self.object_list.count()
        # Проверяем, что на странице необходимое количество новостей:
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        """Сортировка на главной странице."""
        # Получаем даты новостей в том порядке, как они выведены на странице:
        all_dates = [news.date for news in self.object_list]
        # Сортируем полученный список по убыванию:
        sorted_dates = sorted(all_dates, reverse=True)
        # Проверяем, что исходный список был отсортирован правильно:
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):
    """Тестирование комментариев к новости."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаем новость:
        cls.news = News.objects.create(
            title='Тестовая новость', text='Просто текст.'
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('news:detail', args=(cls.news.pk,))
        # Создаем пользователя комментатора:
        cls.author = User.objects.create(username='Комментатор')
        # Запоминаем текущее время:
        now = timezone.now()
        # Создаём комментарии в цикле:
        for index in range(10):
            # Создаём объект и записываем его в переменную:
            comment = Comment.objects.create(
                news=cls.news, author=cls.author, text=f'Tекст {index}',
            )
            # Сразу после создания меняем время создания комментария:
            comment.created = now + timedelta(days=index)
            # И сохраняем эти изменения:
            comment.save()

    def test_comments_order(self):
        """Проверка сортировки комментариев."""
        # GET запрос на страницу новости от анонимного пользователя:
        response = self.client.get(self.detail_url)
        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели:
        self.assertIn('news', response.context)
        # Получаем объект новости:
        news = response.context['news']
        # Получаем все комментарии к новости:
        all_comments = news.comment_set.all()
        # Собираем временные метки всех комментариев:
        all_timestamps = [comment.created for comment in all_comments]
        # Сортируем временные метки, менять порядок сортировки не надо:
        sorted_timestamps = sorted(all_timestamps)
        # Проверяем, что временные метки отсортированы правильно:
        self.assertEqual(all_timestamps, sorted_timestamps)

    def test_anonymous_client_has_no_form(self):
        """Анонимному пользователю форма не передается в контексте."""
        # GET запрос на страницу новости от анонимного пользователя:
        response = self.client.get(self.detail_url)
        # Проверяем, что форма в контексте отсутствует:
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        """Авторизованному пользователю форма передается в контексте."""
        # Авторизуем клиента при помощи ранее созданного пользователя:
        self.client.force_login(self.author)
        # GET запрос на страницу новости от авторизованного пользователя:
        response = self.client.get(self.detail_url)
        # Проверяем, что форма в контексте присутствует:
        self.assertIn('form', response.context)
        # Проверим, что объект формы соответствует нужному классу формы:
        self.assertIsInstance(response.context['form'], CommentForm)
