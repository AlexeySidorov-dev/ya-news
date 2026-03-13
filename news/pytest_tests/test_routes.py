"""Тестирование (pytest) маршрутов проекта yanews."""

import pytest
from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture as lf
from http import HTTPStatus

from django.urls import reverse


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('news:detail', lf('pk_new_for_args')),
        ('users:login', None),
        ('users:signup', None),
        ('users:logout', None),
    ),
)
@pytest.mark.django_db
def test_pages_availability(client, name, args):
    """Доступность страниц для анонимного пользователя."""
    url = reverse(name, args=args)  # Формируем URL.
    # Запрос от имени анонимного пользователя на сформированную страницу:
    if name == 'users:logout':
        response = client.post(url)  # POST запрос.
    else:
        response = client.get(url)
    # Проверяем статус-код:
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        # Автор комментария должен получить ответ OK:
        (lf('author_client'), HTTPStatus.OK),
        # Читатель должен получить ответ NOT_FOUND:
        (lf('reader_client'), HTTPStatus.NOT_FOUND),
    ),
)
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', lf('pk_comment_for_args')),
        ('news:delete', lf('pk_comment_for_args'))
    ),
)
def test_availability_for_comment_edit_and_delete(parametrized_client,
                                                  expected_status, name, args):
    """Доступность страниц по правам пользователя."""
    url = reverse(name, args=args)  # Формируем URL.
    # GET запрос от имени пользователя на сформированную страницу:
    response = parametrized_client.get(url)
    # Проверяем статус-код:
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', lf('pk_comment_for_args')),
        ('news:delete', lf('pk_comment_for_args')),
    ),
)
def test_redirect_for_anonymous_client(client, name, args):
    """Редирект для анонимного пользователя."""
    # Сохраняем адрес страницы логина (перенаправление на нее):
    login_url = reverse('users:login')
    url = reverse(name, args=args)  # Формируем URL.
    redirect_url = f'{login_url}?next={url}'  # Страница редиректа.
    # GET запрос от анонимного пользователя на сформированную страницу:
    response = client.get(url)
    # Проверяем редирект:
    assertRedirects(response, redirect_url)
