"""Тестирование (pytest) логики проекта yanews."""

import pytest
from http import HTTPStatus
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from news.models import Comment
from news.forms import WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, pk_new_for_args,
                                            form_data):
    """Анонимный пользователь не может отправлять комментарии."""
    # Адрес страницы с новостью:
    url = reverse('news:detail', args=pk_new_for_args)
    # POST запрос от анонимного клиента на добавление комментария:
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    # Проверяем, что редирект привёл к странице логина:
    assertRedirects(response, expected_url)
    # Фиксируем в переменной, что комментарий не добавлен:
    count_comment = 0
    # Получаем количество комментариев из БД:
    count_comment_from_db = Comment.objects.count()
    # Убеждаемся, что комментарий не добавлен:
    assert count_comment_from_db == count_comment


def test_user_can_create_comment(author_client, author, pk_new_for_args,
                                 form_data, new):
    """Авторизованный пользователь может отправлять комментарии."""
    # Адрес страницы с новостью:
    url = reverse('news:detail', args=pk_new_for_args)
    # POST запрос от авторизованного клиента на добавление комментария:
    response = author_client.post(url, data=form_data)
    # Адрес раздела с комментариями:
    url_to_comments = f'{url}#comments'
    # Проверяем, что редирект привёл к разделу с комментариями:
    assertRedirects(response, url_to_comments)
    # Фиксируем в переменной, что комментарий добавлен:
    count_comment = 1
    # Получаем количество комментариев из БД:
    count_comment_from_db = Comment.objects.count()
    # Убеждаемся, что комментарий добавлен:
    assert count_comment_from_db == count_comment
    # Получаем объект комментария из БД:
    comment = Comment.objects.get(news=new)
    # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
    assert comment.text == form_data['text']
    assert comment.news == new
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, pk_new_for_args,
                                 bad_words_data):
    """Проверка запрещенных слов в комментарии."""
    # Адрес страницы с новостью:
    url = reverse('news:detail', args=pk_new_for_args)
    # POST запрос от авторизованного клиента на добавление комментария, в форме
    # добавлено слово исключение:
    response = author_client.post(url, data=bad_words_data)
    # Получаем форму из контекста:
    form = response.context['form']
    # Проверяем, есть ли в ответе ошибка формы:
    assertFormError(form=form, field='text', errors=WARNING)
    # Фиксируем в переменной, что комментарий не добавлен:
    count_comment = 0
    # Получаем количество комментариев из БД:
    count_comment_from_db = Comment.objects.count()
    # Убеждаемся, что комментарий не добавлен:
    assert count_comment_from_db == count_comment


def test_author_can_delete_comment(author_client, pk_comment_for_args,
                                   pk_new_for_args):
    """Автор может удалять свой комментарий."""
    # Адрес страницы удаления комментария:
    url = reverse('news:delete', args=pk_comment_for_args)
    # От имени автора комментария отправляем DELETE-запрос на удаление:
    response = author_client.delete(url)
    # Адрес страницы с новостью:
    news_url = reverse('news:detail', args=pk_new_for_args)
    # Адрес раздела с комментариями:
    url_to_comments = f'{news_url}#comments'
    # Проверяем, что редирект привёл к разделу с комментариями:
    assertRedirects(response, url_to_comments)
    # Проверяем статус-код:
    assert response.status_code == HTTPStatus.FOUND
    # Фиксируем в переменной, что комментарий удален:
    count_comment = 0
    # Получаем количество комментариев из БД:
    count_comment_from_db = Comment.objects.count()
    # Убеждаемся, что комментарий удален:
    assert count_comment_from_db == count_comment


def test_author_can_edit_comment(author_client, pk_comment_for_args,
                                 pk_new_for_args, form_data_edit, comment):
    """Автор может редактировать свой комментарий."""
    # Адрес страницы для редактирования комментария:
    url = reverse('news:edit', args=pk_comment_for_args)
    # POST запрос на редактирование от имени автора комментария:
    response = author_client.post(url, data=form_data_edit)
    # Адрес страницы с новостью:
    news_url = reverse('news:detail', args=pk_new_for_args)
    # Адрес раздела с комментариями.
    url_to_comments = f'{news_url}#comments'
    # Проверяем, что редирект привёл к разделу с комментариями:
    assertRedirects(response, url_to_comments)
    # Обновляем объект комментария:
    comment.refresh_from_db()
    # Проверяем, что текст комментария соответствует обновленному:
    assert comment.text == form_data_edit['text']


def test_user_cant_delete_comment_of_another_user(reader_client,
                                                  pk_comment_for_args):
    """Пользователь не может удалить комментарий другого автора."""
    # Адрес страницы удаления комментария:
    url = reverse('news:delete', args=pk_comment_for_args)
    # DELETE запрос на удаление от пользователя-читателя:
    response = reader_client.delete(url)
    # Проверяем, что вернулась 404 ошибка:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Фиксируем в переменной, что комментарий не удален:
    count_comment = 1
    # Получаем количество комментариев из БД:
    count_comment_from_db = Comment.objects.count()
    # Убеждаемся, что комментарий не удален:
    assert count_comment_from_db == count_comment


def test_user_cant_edit_comment_of_another_user(
        reader_client, pk_comment_for_args, form_data_edit, comment):
    """Пользователь не может редактировать комментарий другого автора."""
    # Адрес страницы для редактирования комментария:
    url = reverse('news:edit', args=pk_comment_for_args)
    # POST запрос на редактирование от имени другого пользователя:
    response = reader_client.post(url, data=form_data_edit)
    # Проверяем, что вернулась 404 ошибка:
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Обновляем объект комментария:
    comment.refresh_from_db()
    # Проверяем, что текст комментария не изменился:
    assert comment.text != form_data_edit['text']
