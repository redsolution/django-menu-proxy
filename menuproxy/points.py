def get_catalog():
    u"""Возвращает элемент pages к которому будет подключен каталог"""
    from pages.utils import get_page_from_slug
    return get_page_from_slug('catalog')


def get_news():
    u"""Возвращает элемент pages к которому будет подключены новости"""
    from pages.utils import get_page_from_slug
    return get_page_from_slug('news')
