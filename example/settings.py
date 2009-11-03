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
MENU_PROXY_RULES = {}
MENU_PROXY_RULES['page'] = {
    'method': 'root',
    'proxy': 'menuproxy.proxies.MenuProxy',
    'model': 'example.models.Page',
}
MENU_PROXY_RULES['catalog'] = {
    'method': 'append',
    'inside': 'page',
    'point': 'example.points.get_catalog_page',
    'proxy': 'menuproxy.proxies.MenuProxy',
    'model': 'example.models.Catalog',
    'children_filter': {'visible': True, },
}
MENU_PROXY_RULES['archive'] = {
    'method': 'instead',
    'inside': 'page',
    'point': 'example.points.get_news_page',
    'proxy': 'menuproxy.proxies.ReverseProxy',
    'args': ['archive', ],
    'get_title': 'example.points.get_news_name',
}
MENU_PROXY_RULES['news'] = {
    'method': 'append',
    'inside': 'archive',
    'proxy': 'menuproxy.proxies.FlatProxy',
    'model': 'example.models.News',
}
MENU_PROXY_RULES['search'] = {
    'method': 'instead',
    'inside': 'page',
    'point': 'example.points.get_search_page',
    'proxy': 'menuproxy.proxies.ReverseProxy',
    'args': ['search', ],
    'get_title': 'example.points.get_search_name',
}
