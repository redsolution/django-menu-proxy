# -*- coding: utf-8 -*-

from django import conf
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

def import_item(path, error_text):
    u"""Импортирует по указанному пути. В случае ошибки генерируется исключение с указанным текстом"""
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        return getattr(__import__(module, {}, {}, ['']), attr)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing %s %s: "%s"' % (error_text, path, e))

def get_title(menu_proxy, model, obj):
    u"""Корректировка значения, возвращаемого функцией title"""
    if obj is None:
        return u''
    result = menu_proxy.title(model, obj)
    if result is None:
        return u''
    return unicode(result)

def get_url(menu_proxy, model, obj):
    u"""Корректировка значения, возвращаемого функцией url"""
    if obj is None:
        return u''
    result = menu_proxy.url(model, obj)
    if result is None:
        return u''
    return unicode(result)

def get_ancestors(menu_proxy, model, obj):
    u"""Корректировка значения, возвращаемого функцией ancestors"""
    if obj is None:
        return []
    result = menu_proxy.ancestors(model, obj)
    if result is None:
        return []
    return result

def get_children(menu_proxy, model, obj, force):
    u"""Корректировка значения, возвращаемого функцией children"""
    result = menu_proxy.children(model, obj, force)
    if result is None:
        return []
    return result

class MenuItem(object):
    u"""Класс элементов меню, передаваемых в шаблоны, умеющих работать сквозь все зарегистрированные меню"""
    
    active = False
    current = False

    def __init__(self, settings, proxy, model, obj):
        self.settings = settings
        self.proxy = proxy
        self.model = model
        self.obj = obj
        
    def title(self):
        u"""Возвращает заголовок элемента меню"""
        if hasattr(self, '_title'):
            return getattr(self, '_title')
        title = get_title(self.proxy, self.model, self.obj)
        setattr(self, '_title', title)
        return title
            
    def url(self):
        u"""Возвращает url элемента меню"""
        if hasattr(self, '_url'):
            return getattr(self, '_url')
        url = get_url(self.proxy, self.model, self.obj)
        setattr(self, '_url', url)
        return url

    def ancestors(self):
        u"""Возвращает список родительских элементов меню, начиная с верхнего уровня"""
        if hasattr(self, '_ancestors'):
            return getattr(self, '_ancestors')
        proxy = self.proxy
        model = self.model
        obj = self.obj
        ancestors = []
        while True:
            ancestors = [MenuItem(self.settings, proxy, model, item)
                for item in get_ancestors(proxy, model, obj)] + ancestors
            for setting in self.settings:
                if setting['model'] == model and setting['point'] is not None:
                    obj = setting['point']
                    model = obj.__class__
                    proxy = get_proxy(self.settings, obj)
                    break
            else:
                break
        setattr(self, '_ancestors', ancestors)
        return ancestors

    def children(self, force):
        u"""Возвращает список дочерних элементов меню"""
        if hasattr(self, '_children'):
            return getattr(self, '_children')
        proxy = self.proxy
        model = self.model
        obj = self.obj
        for setting in self.settings:
            if obj == setting['point']:
                proxy = setting['proxy']
                model = setting['model']
                obj = None
                break
        children = [MenuItem(self.settings, proxy, model, item)
            for item in get_children(proxy, model, obj, force)]
        setattr(self, '_children', children)
        return children

def get_settings():
    u"""Получает список настроек меню"""
    settings = cache.get('menuproxy.settings', None)
    if settings is not None:
        return settings

    settings = []
    for model, proxy, point in getattr(conf.settings, 'MENU_PROXY_SETTINGS', []):
        item = {}
        item['model'] = import_item(model, 'model')
        for setting in settings:
            if setting['model'] == item['model']:
                raise ImproperlyConfigured('menuproxy does`t support more than one same model')
        item['proxy'] = import_item(proxy, 'MenuProxy class')()
        if point is None:
            item['point'] = None
        else:
            item['point'] = import_item(point, 'mount point function')()
        for setting in settings:
            if setting['point'] == item['point'] and item['point'] is not None:
                raise ImproperlyConfigured('menuproxy does`t support more than one similar point %r' % item['point'])
        if point is None:
            settings.insert(0, item)
        else:
            settings.append(item)
    for setting in settings:
        if setting['point'] is None:
            break
    else:
        raise ImproperlyConfigured('menuproxy must have root (with None as point)')

    cache.set('menuproxy.settings', settings)
    return settings

def get_proxy(settings, obj):
    u"""Получает MenuProxy для указанного объекта"""
    for setting in settings:
        if obj.__class__ == setting['model']:
            return setting['proxy']
    return None

def get_item(settings, obj):
    u"""Получает MenuItem для указанного объекта"""
    if isinstance(obj, MenuItem):
        return obj
    if obj is None:
        proxy = settings[0]['proxy']
        model = settings[0]['model']
    else:
        proxy = get_proxy(settings, obj)
        model = obj.__class__
    return MenuItem(settings, proxy, model, obj)


