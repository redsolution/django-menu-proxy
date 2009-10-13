# -*- coding: utf-8 -*-

from django import conf
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
import importpath

def get_title(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией title"""
    if obj is None:
        return u''
    result = menu_proxy.title(obj)
    if result is None:
        return u''
    return unicode(result)

def get_url(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией url"""
    if obj is None:
        return u''
    result = menu_proxy.url(obj)
    if result is None:
        return u''
    return unicode(result)

def get_ancestors(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией ancestors"""
    if obj is None:
        return []
    result = menu_proxy.ancestors(obj)
    if result is None:
        return []
    return [value for value in result]

def get_children(menu_proxy, obj, force):
    u"""Корректировка значения, возвращаемого функцией children или force"""
    if force:
        result = menu_proxy.force(obj)
    else:
        result = menu_proxy.children(obj)
    if result is None:
        return []
    return [value for value in result]

def try_to_import(dictionary, key, exception_text):
    u"""Если значение key задано, пытаемся импортировать указанный объект"""
    value = setting.get(key, None)
    if not value is None:
        value = importpath(value, exception_text)
    setting[key] = value

class MenuSettings(object):
    u"""Класс для хранения настроек menuproxy в подготовленном формате"""
    METHODS = (
        'root', # Указывает корневое дерево для построения меню
        'instead', # Указывает, что объект point следует заменить объектом object
        'append', # Указывает, что к списку дочерних элементов для point нужно добавить дочерние элементы object-а 
        'prepend', # Указывает, что перед списком дочерних элементов для point нужно вставить дочерние элементы object-а
    )
    
    def __init__(self):
        self.root = None
        self.instead = {}
        self.append = {}
        self.prepend = {}
        self.settings = getattr(conf.settings, 'MENU_PROXY', {})
        
        for name, setting in self.settings.iteritems():
            if setting['method'] not in self.METHODS:
                raise ImproperlyConfigured('menuproxy does`t support method: %s', setting['method'])
            if 'proxy' not in setting:
                raise ImproperlyConfigured('menuproxy need proxy for %s setting' % name)

            setting['name'] = name
            setting['inside'] = setting.get('inside', None)
            try_to_import(setting, 'model', 'model class')
            try_to_import(setting, 'point', 'mount point function')
            try_to_import(setting, 'object', 'mount object function')
            setting['proxy'] = importpath(setting['proxy'], 'MenuProxy class')(setting)
            if setting['method'] == 'root':
                if self.root is not None:
                    raise ImproperlyConfigured('menuproxy does`t support more that one method "root"')
                setting['inside'] = None
                setting['point'] = None
                root = setting
            if setting['method'] == 'root':
                key = (setting['inside'], setting['point'])
                dictionary = getattr(self, setting['method'])
                if key in dictionary:
                    continue
                dictionary[key] = setting

        if self.root is None:
            raise ImproperlyConfigured('menuproxy must have setting with method "root"')

        self.top = get_children(self.root['proxy'], self.root['model'], False)
        
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
    
    def __init__(self, name, obj):
        self.source = []
        while (name, obj) in self.settings.instead:
            self.source.append((name, obj))
            instead = self.settings.instead[name, obj]
            name = instead['inside']
            obj = instead['object']
        self.name = name
        self.obj = obj
        
    def title(self):
        u"""Возвращает заголовок элемента меню"""
        if hasattr(self, '_title'):
            return getattr(self, '_title')
        title = get_title(self.get('proxy'), self.obj)
        setattr(self, '_title', title)
        return title
            
    def url(self):
        u"""Возвращает url элемента меню"""
        if hasattr(self, '_url'):
            return getattr(self, '_url')
        url = get_url(get_settings().settings[self.name]['proxy'], self.obj)
        setattr(self, '_url', url)
        return url

    def ancestors(self):
        u"""Возвращает список родительских элементов меню, начиная с верхнего уровня"""
        if hasattr(self, '_ancestors'):
            return getattr(self, '_ancestors')
        
        settings = get_settings().settings
        ancestors = []
        name = self.name
        obj = self.obj
        while True:
            until = self.get('object')
            items = get_ancestors(settings[name]['proxy'], obj)
            items.reverse()
            items.append(until)
            for item in items:
                if item != until:
                    ancestors.insert(0, MenuItem(name, item))
                elif settings[name]['point'] is not None:
                    method = settings[name]['method']
                    if method == 'instead':
                        ancestors.insert(0, MenuItem(name, item))
                    obj = settings[name]['point']
                    name = settings[name]['inside']
                    if method != 'instead':
                        ancestors.insert(0, MenuItem(name, obj))
                    break
            else:
                break
            
        front_page = get_settings().front_page
        
        if front_page is not None:
            if not ancestors or ancestors[0].obj != front_page:
                ancestors.insert(0, MenuItem(get_settings().root['name'], front_page))
        setattr(self, '_ancestors', ancestors)
        return ancestors

    def children(self, force):
        u"""Возвращает список дочерних элементов меню"""
        if hasattr(self, '_children'):
            return getattr(self, '_children')
        
        key = (self.name, self.obj)
        prepend = get_settings().prepend
        append = get_settings().append
        children = []
        if key in prepend:
            children += [
                MenuItem(prepend[key]['name'], item) for item in get_children(
                    prepend[key]['proxy'], prepend[key]['object'], force)
            ]
        children += [
            MenuItem(self.name) for item in get_children(
                get_settings().settings[self.name]['proxy'], self.obj, force)
        ]
        if key in append:
            children += [
                MenuItem(prepend[key]['name'], item) for item in get_children(
                    append[key]['proxy'], append[key]['object'], force)
            ]

        setattr(self, '_children', children)
        return children
    

def get_item(settings, obj):
    u"""Получает MenuItem для указанного объекта"""
    if isinstance(obj, MenuItem):
        return obj
    if obj is None:
        model = settings.root['model']
        proxy = settings.root['proxy']
    else:
        model = obj.__class__
        proxy = settings.models[model]['proxy']
    return MenuItem(settings, proxy, model, obj)
