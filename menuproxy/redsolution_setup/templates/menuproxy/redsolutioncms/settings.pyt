# ---- django-menuproxy ----

INSTALLED_APPS += ['menuproxy']

try:
    MENU_PROXY_RULES
except NameError:
    MENU_PROXY_RULES = []
