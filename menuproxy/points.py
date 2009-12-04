# -*- coding: utf-8 -*-
def get_page_object(slug):
    u"""Возвращает элемент pages со слагом slug"""
    from pages.models import Page
    from pages.settings import PAGE_DEFAULT_LANGUAGE
    result = Page.objects.from_path(slug, PAGE_DEFAULT_LANGUAGE)
    if result is not None:
        return result
    return Page.DoesNotExist

def get_page_title(slug):
    u"""Возвращает заголовок элемент pages со слагом slug"""
    from pages.models import Page
    from pages.settings import PAGE_DEFAULT_LANGUAGE
    result = Page.objects.from_path(slug, PAGE_DEFAULT_LANGUAGE)
    if result is not None:
        return result.title()
    return ''

def get_news_page():
    u"""Возвращает элемент pages к которому будет подключены новости"""
    return get_page_object('news')

def get_news_name():
    u"""Возвращает title элемента pages к которому будет подключены новости"""
    return get_page_title('news')

def get_catalog_page():
    u"""Возвращает элемент pages к которому будет подключен каталог"""
    return get_page_object('catalog')

def get_catalog_name():
    u"""Возвращает title элемента pages к которому будет подключены новости"""
    return get_page_title('catalog')

def get_search_page():
    u"""Возвращает элемент pages к которому будет подключен поиск"""
    return get_page_object('search')

def get_search_name():
    u"""Возвращает title элемента pages к которому будет подключены новости"""
    return get_page_title('search')
