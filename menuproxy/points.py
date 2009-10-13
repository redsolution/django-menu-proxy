def get_news_page():
    u"""Возвращает элемент pages к которому будет подключены новости"""
    from pages.models import Page
    from pages.settings import PAGE_DEFAULT_LANGUAGE
    return Page.objects.from_path('news', PAGE_DEFAULT_LANGUAGE)

def get_catalog_page():
    u"""Возвращает элемент pages к которому будет подключен каталог"""
    from pages.models import Page
    from pages.settings import PAGE_DEFAULT_LANGUAGE
    return Page.objects.from_path('catalog', PAGE_DEFAULT_LANGUAGE)
