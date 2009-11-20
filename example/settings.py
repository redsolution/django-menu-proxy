import os

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'menuproxy.sqlite'
SITE_ID = 1

SECRET_KEY = '(smqgqqzm*4^w^d==jm#$=f^qgb3+_+mst3@smq+ghfclwp**a'

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'example.middleware.ConsoleExceptionMiddleware',
]

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
)

ROOT_URLCONF = 'example.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'menuproxy',
    'example',
)

# MenuProxy settings
MENU_PROXY_RULES = [
    {
        'name': 'page',
        'method': 'children',
        'proxy': 'menuproxy.proxies.MenuProxy',
        'model': 'example.models.Page',
    },
    {
        'name': 'catalog',
        'method': 'children',
        'proxy': 'menuproxy.proxies.MenuProxy',
        'inside': 'page',
        'point': 'example.points.get_catalog_page',
        'model': 'example.models.Catalog',
        'children_filter': {'visible': True, },
    },
    {
        'name': 'archive',
        'method': 'replace',
        'inside': 'page',
        'point': 'example.points.get_news_page',
        'proxy': 'menuproxy.proxies.ReverseProxy',
        'viewname': 'archive',
        'get_title': 'example.points.get_news_name',
    },
    {
        'name': 'news',
        'method': 'children',
        'inside': 'archive',
        'proxy': 'menuproxy.proxies.FlatProxy',
        'model': 'example.models.News',
    },
    {
        'name': 'search',
        'method': 'replace',
        'inside': 'page',
        'point': 'example.points.get_search_page',
        'proxy': 'menuproxy.proxies.ReverseProxy',
        'viewname': 'search',
        'get_title': 'example.points.get_search_name',
    },
    {
        'name': 'result',
        'method': 'insert',
        'inside': 'search',
        'proxy': 'menuproxy.proxies.ReverseProxy',
        'viewname': 'result',
        'title_text': 'Results',
    },
]
