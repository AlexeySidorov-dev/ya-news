"""Фикстуры pytest."""

import pytest
from datetime import datetime, timedelta
from django.conf import settings
from django.test.client import Client
from django.utils import timezone

from news.models import Comment, News
from news.forms import BAD_WORDS


@pytest.fixture
def author(django_user_model):
    """Создаем пользователя автора."""
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def reader(django_user_model):
    """Создаем пользователя читателя."""
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def author_client(author):
    """Логиним автора в клиенте."""
    # Создаём новый экземпляр клиента, чтобы не менять глобальный.
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    """Логиним читателя в клиенте."""
    client = Client()
    client.force_login(reader)
    return client


@pytest.fixture
def all_news():
    """Создаем список новостей (11 штук)."""
    today = datetime.today()
    all_news = [
        News(title=f'Новость {index}',
             text='Просто текст.',
             # Для каждой новости уменьшаем дату на index дней от today,
             # где index - счётчик цикла.
             date=today - timedelta(days=index)
             )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    return all_news


@pytest.fixture
def all_comments(author, all_news):
    """Создаем 10 комментариев к первой новости от пользователя автора."""
    new = all_news[0]  # Первая новость из списка новостей.
    # Запоминаем текущее время:
    now = timezone.now()
    # Создаём комментарии в цикле.
    for index in range(10):
        # Создаём объект и записываем его в переменную.
        comment = Comment.objects.create(
            news=new, author=author, text=f'Tекст {index}',
        )
        # Сразу после создания меняем время создания комментария.
        comment.created = now + timedelta(days=index)
        # И сохраняем эти изменения.
        comment.save()
    return comment  # Возвращаем последний комментарий для тестов.


@pytest.fixture
def pk_new_for_args(all_news):
    """Получаем из первой новости кортеж с ее pk."""
    new = all_news[0]  # Первая новость из списка новостей.
    return (new.pk,)


@pytest.fixture
def pk_comment_for_args(all_comments):
    """Получаем из первого комментария кортеж с его pk."""
    return (all_comments.pk,)


@pytest.fixture
def form_data():
    """Формируем данные для отправки формы комментария."""
    return {'text': 'Текст комментария'}


@pytest.fixture
def form_data_edit():
    """Формируем данные для отправки формы редактирования комментария."""
    return {'text': 'Редактированный текст комментария'}


@pytest.fixture
def bad_words_data():
    """Формируем данные для отправки формы комментария с плохим словом."""
    return {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
