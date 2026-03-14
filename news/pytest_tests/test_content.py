"""Тестирование (pytest) контента проекта yanews."""

import pytest
from django.urls import reverse
from django.conf import settings

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count_and_order(client, all_news):
    """Проверка главной страницы на сортировку и количество новостей."""
    url = reverse('news:home')  # Главная страница.
    # GET запрос от анонимного пользователя на главную страницу:
    response = client.get(url)
    # Получаем список объектов из словаря контекста:
    object_list = response.context['object_list']

    # Определяем количество новостей в списке:
    news_count = object_list.count()
    # Проверяем, что на странице нужное количество новостей:
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE

    # Получаем даты новостей в том порядке, как они выведены на странице:
    all_dates = [news.date for news in object_list]
    # Сортируем полученный список по убыванию:
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что исходный список был отсортирован правильно:
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, pk_new_for_args):
    """Проверка сортировки комментариев."""
    # Страница отдельной новости с комментариями:
    url = reverse('news:detail', args=pk_new_for_args)
    # GET запрос на страницу отдельной новости от анонимного пользователя:
    response = client.get(url)
    # Проверяем, что объект новости находится в словаре контекста
    # под ожидаемым именем - названием модели.
    assert 'news' in response.context
    # Получаем объект новости.
    new = response.context['news']
    # Получаем все комментарии к новости из БД:
    all_comments = new.comment_set.all()
    # Собираем временные метки всех комментариев.
    all_timestamps = [comment.created for comment in all_comments]
    # Сортируем временные метки, менять порядок сортировки не надо.
    sorted_timestamps = sorted(all_timestamps)
    # Проверяем, что временные метки отсортированы правильно.
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, pk_new_for_args):
    """Анонимному пользователю форма не передается в контексте."""
    # Сохраняем в переменную адрес страницы с новостью:
    url = reverse('news:detail', args=pk_new_for_args)
    # GET запрос на страницу новости от анонимного пользователя:
    response = client.get(url)
    # Проверяем, что форма в контексте отсутствует:
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, pk_new_for_args):
    """Авторизованному пользователю форма передается в контексте."""
    # Сохраняем в переменную адрес страницы с новостью:
    url = reverse('news:detail', args=pk_new_for_args)
    # GET запрос на страницу новости от авторизованного пользователя:
    response = author_client.get(url)
    # Проверяем, что форма в контексте присутствует:
    assert 'form' in response.context
    # Проверим, что объект формы соответствует нужному классу формы.
    assert isinstance(response.context['form'], CommentForm)
