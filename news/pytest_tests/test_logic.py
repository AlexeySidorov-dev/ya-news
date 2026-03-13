"""Тестирование (pytest) логики проекта yanews."""

import pytest
from http import HTTPStatus
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from news.models import Comment
from news.forms import WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, pk_new, form_data):
    """Анонимный пользователь не может оставлять комментарии."""
    # Адрес страницы с новостью.
    url = reverse('news:detail', args=pk_new)
    # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
    # предварительно подготовленные данные формы с текстом комментария.
    client.post(url, data=form_data)
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
    assert comments_count == 0


def test_user_can_create_comment(author_client, author, pk_new, form_data,
                                 all_news):
    """Авторизованный пользователь может оставлять комментарии."""
    # Адрес страницы с новостью.
    url = reverse('news:detail', args=pk_new)
    # Совершаем запрос через авторизованный клиент.
    response = author_client.post(url, data=form_data)
    # Проверяем, что редирект привёл к разделу с комментами.
    assertRedirects(response, f'{url}#comments')
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Убеждаемся, что есть один комментарий.
    assert comments_count == 1
    # Получаем объект комментария из базы.
    comment = Comment.objects.get()
    # Первая новость, которую используем в тесте.
    new = all_news[0]
    # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
    assert comment.text == form_data['text']
    assert comment.news == new
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, pk_new, bad_words_data):
    """Проверка плохих слов в комментарии."""
    # Адрес страницы с новостью.
    url = reverse('news:detail', args=pk_new)
    # Отправляем запрос через авторизованный клиент.
    response = author_client.post(url, data=bad_words_data)
    form = response.context['form']
    # Проверяем, есть ли в ответе ошибка формы.
    assertFormError(form=form, field='text', errors=WARNING)
    # Дополнительно убедимся, что комментарий не был создан.
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(author_client, pk_comment, pk_new):
    """Автор может удалить свой комментарий."""
    # Адрес страницы удаления комментария.
    url = reverse('news:delete', args=pk_comment)
    # От имени автора комментария отправляем DELETE-запрос на удаление.
    response = author_client.delete(url)
    # Адрес новости.
    news_url = reverse('news:detail', args=pk_new)
    # Адрес блока с комментариями.
    url_to_comments = news_url + '#comments'
    # Проверяем, что редирект привёл к разделу с комментариями.
    assertRedirects(response, url_to_comments)
    # Заодно проверим статус-коды ответов.
    assert response.status_code == HTTPStatus.FOUND
    # Считаем количество комментариев в системе.
    comments_count = Comment.objects.count()
    # Ожидаем ноль комментариев в системе.
    assert comments_count == 9  # Всего было  создано для теста 10.


def test_user_cant_delete_comment_of_another_user(reader_client, pk_comment):
    """Пользователь не может удалить комментарий другого автора."""
    # Адрес страницы удаления комментария.
    url = reverse('news:delete', args=pk_comment)
    # Выполняем запрос на удаление от пользователя-читателя.
    response = reader_client.delete(url)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что комментарий по-прежнему на месте.
    comments_count = Comment.objects.count()
    assert comments_count == 10  # Всего было  создано для теста 10.


def test_author_can_edit_comment(author_client, pk_comment, pk_new,
                                 form_data_edit):
    """Автор может редактировать свой комментарий."""
    # URL для редактирования комментария.
    url = reverse('news:edit', args=pk_comment)
    # Выполняем запрос на редактирование от имени автора комментария.
    response = author_client.post(url, data=form_data_edit)
    # Адрес новости.
    news_url = reverse('news:detail', args=pk_new)
    # Адрес блока с комментариями.
    url_to_comments = news_url + '#comments'
    # Проверяем, что сработал редирект.
    assertRedirects(response, url_to_comments)
    # Получаем объект комментария по его pk, первое значение из кортежа.
    comment = Comment.objects.get(pk=pk_comment[0])
    # Проверяем, что текст комментария соответствует обновленному.
    assert comment.text == form_data_edit['text']


def test_user_cant_edit_comment_of_another_user(reader_client, pk_comment,
                                                form_data_edit):
    """Пользователь не может редактировать комментарий другого автора."""
    # URL для редактирования комментария.
    url = reverse('news:edit', args=pk_comment)
    # Выполняем запрос на редактирование от имени другого пользователя.
    response = reader_client.post(url, data=form_data_edit)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем объект комментария по его pk, первое значение из кортежа.
    comment = Comment.objects.get(pk=pk_comment[0])
    # Проверяем, что текст не изменился.
    assert comment.text != form_data_edit['text']
