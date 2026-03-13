"""Тестирование (pytest) контента проекта yanews."""

import pytest
from pytest_lazyfixture import lazy_fixture as lf
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, all_news):
    """Проверка главной страницы на сортировку и количество новостей."""
    url = reverse('news:home')
    # Загружаем главную страницу.
    response = client.get(url)
    # Получаем список объектов из словаря контекста.
    object_list = response.context['object_list']

    # Определяем количество записей в списке.
    news_count = object_list.count()
    # Проверяем, что на странице именно 10 новостей.
    assert news_count == (len(all_news) - 1)

    # Получаем даты новостей в том порядке, как они выведены на странице.
    all_dates = [news.date for news in object_list]
    # Сортируем полученный список по убыванию.
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что исходный список был отсортирован правильно.
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, pk_new):
    """Проверка сортировки комментариев."""
    url = reverse('news:detail', args=pk_new)
    response = client.get(url)
    # Проверяем, что объект новости находится в словаре контекста
    # под ожидаемым именем - названием модели.
    assert 'news' in response.context
    # Получаем объект новости.
    news = response.context['news']
    # Получаем все комментарии к новости.
    all_comments = news.comment_set.all()
    # Собираем временные метки всех комментариев.
    all_timestamps = [comment.created for comment in all_comments]
    # Сортируем временные метки, менять порядок сортировки не надо.
    sorted_timestamps = sorted(all_timestamps)
    # Проверяем, что временные метки отсортированы правильно.
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, pk_new):
    """Анонимному пользователю форма не передается в контексте."""
    url = reverse('news:detail', args=pk_new)
    response = client.get(url)
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, pk_new):
    """Авторизованному пользователю форма передается в контексте."""
    url = reverse('news:detail', args=pk_new)
    response = author_client.get(url)
    assert 'form' in response.context
    # Проверим, что объект формы соответствует нужному классу формы.
    assert isinstance(response.context['form'], CommentForm)
