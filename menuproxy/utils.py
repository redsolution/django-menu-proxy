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
    return [value for value in result]

def get_children(menu_proxy, model, obj, force):
    u"""Корректировка значения, возвращаемого функцией children"""
    result = menu_proxy.children(model, obj, force)
    if result is None:
        return []
    return [value for value in result]

class MenuSettings(object):
    u"""Класс для хранения настроек menuproxy в подготовленном формате"""
    METHODS = (
        'root', # Указывает корневое дерево для построения меню
        'instead', # Указывает, что объект point следует заменить объектом object
        'append', # Указывает, что к списку дочерних элементов для point нужно добавить дочерние элементы object-а 
        'prepend', # Указывает, что перед списком дочерних элементов для point нужно вставить дочерние элементы object-а
    )
    
    def __init__(self):
        self.root = {}
        self.instead = {}
        self.append = {}
        self.prepend = {}
        self.models = {} # Используемые модели
        
        for setting in getattr(conf.settings, 'MENU_PROXY_SETTINGS', []):
            if setting['method'] not in self.METHODS:
                raise ImproperlyConfigured('menuproxy does`t support method: %s', setting['method'])

            model = import_item(setting['model'], 'model class')

            proxy = import_item(setting['proxy'], 'MenuProxy class')()

            
            if setting.get('point', None) is None:
                point = None
            else:
                point = import_item(setting['point'], 'mount point function')()

            if setting.get('object', None) is None:
                obj = None
            else:
                obj = import_item(setting['object'], 'mount object function')()
                
            if setting['method'] == 'root':
                point = None
            elif point is None:
                continue # menuproxy must know the point for mounting, so skip it
            
            if setting['method'] == 'instead' and object is None:
                continue # menuproxy must know the object for mounting, so skip it

            dictionary = getattr(self, setting['method'])
            if point in dictionary:
                continue
            dictionary[point] = {'model': model, 'proxy': proxy, 'object': obj, }

            if model in self.models:
                raise ImproperlyConfigured('menuproxy does`t support more than one same model')
            else:
                self.models[model] = {'proxy': proxy, 'object': obj, 'point': point, }

        if None not in self.root:
            raise ImproperlyConfigured('menuproxy must have setting with method: root')

        self.top = get_children(self.root[None]['proxy'], self.root[None]['model'], None, True)
        
        if getattr(conf.settings, 'MENU_PROXY_FRONT_PAGED', False) and self.top:
            self.front_page = self.top[0]
        else:
            self.front_page = None



def get_settings():
    u"""Получает список настроек меню"""
    settings = cache.get('menuproxy.settings', None)
    if settings is not None:
        return settings
    settings = MenuSettings()
    cache.set('menuproxy.settings', settings)
    return settings


class MenuItem(object):
    u"""Класс элементов меню, передаваемых в шаблоны, умеющих работать сквозь все зарегистрированные меню"""
    
    active = False
    current = False

    def __init__(self, settings, proxy, model, obj):
        self.settings = settings
        if obj in self.settings.instead:
            self.proxy = self.settings.instead[obj]['proxy']
            self.model = self.settings.instead[obj]['model']
            self.obj = self.settings.instead[obj]['object']
            print obj, ' -> ', self.obj
        else:
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
        
        ancestors = []
        proxy = self.proxy
        model = self.model
        obj = self.obj
        ancestors = []
        while model in self.settings.models:
            until = self.settings.models[model]['object']
            items = get_ancestors(proxy, model, obj)
            items.reverse()
            items.append(None) 
            for item in items:
                if item != until:
                    ancestors.insert(0, MenuItem(self.settings, proxy, model, item))
                elif self.settings.models[model]['point'] is not None:
                    obj = self.settings.models[model]['point']
                    model = self.settings.models[model]['point'].__class__
                    proxy = self.settings.models[model]['proxy']
                    break
            else:
                break
        if self.settings.front_page is not None:
            if not ancestors or ancestors[0].obj != self.settings.front_page:
                ancestors.insert(0, MenuItem(
                    self.settings, 
                    self.settings.root[None]['proxy'],
                    self.settings.root[None]['model'],
                    self.settings.front_page))
        setattr(self, '_ancestors', ancestors)
        return ancestors

    def children(self, force):
        u"""Возвращает список дочерних элементов меню"""
        if hasattr(self, '_children'):
            return getattr(self, '_children')
        
        children = []
        if self.obj in self.settings.prepend:
            children += [
                MenuItem(
                    self.settings, 
                    self.settings.prepend[self.obj]['proxy'], 
                    self.settings.prepend[self.obj]['model'], 
                    item
                ) for item in get_children(
                    self.settings.prepend[self.obj]['proxy'], 
                    self.settings.prepend[self.obj]['model'], 
                    self.settings.prepend[self.obj]['object'],
                    force
                )
            ]
        children += [
            MenuItem(
                self.settings, 
                self.proxy, 
                self.model, 
                item
            ) for item in get_children(
                self.proxy, 
                self.model, 
                self.obj,
                force
            )
        ]
        if self.obj in self.settings.append:
            children += [
                MenuItem(
                    self.settings, 
                    self.settings.append[self.obj]['proxy'], 
                    self.settings.append[self.obj]['model'], 
                    item
                ) for item in get_children(
                    self.settings.append[self.obj]['proxy'], 
                    self.settings.append[self.obj]['model'], 
                    self.settings.append[self.obj]['object'],
                    force
                )
            ]

        setattr(self, '_children', children)
        return children
    

def get_item(settings, obj):
    u"""Получает MenuItem для указанного объекта"""
    if isinstance(obj, MenuItem):
        return obj
    if obj is None:
        model = settings.root[None]['model']
        proxy = settings.root[None]['proxy']
    else:
        model = obj.__class__
        proxy = settings.models[model]['proxy']
    return MenuItem(settings, proxy, model, obj)
