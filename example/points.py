def get_news_page():
    from example.models import Page
    return Page.objects.get(slug='news')

def get_news_name():
    return get_news_page().title

def get_catalog_page():
    from example.models import Page
    return Page.objects.get(slug='catalog')

def get_catalog_name():
    return get_catalog_page().title

def get_search_page():
    from example.models import Page
    return Page.objects.get(slug='search')

def get_search_name():
    return get_search_page().title
