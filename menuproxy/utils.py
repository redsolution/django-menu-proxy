# -*- coding: utf-8 -*-

from django import conf
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from importpath import importpath

def get_title(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией title"""
    result = menu_proxy.title(obj)
    if result is None:
        return u''
    return unicode(result)

def get_url(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией url"""
    result = menu_proxy.url(obj)
    if result is None:
        return u''
    return unicode(result)

def get_ancestors(menu_proxy, obj):
    u"""Корректировка значения, возвращаемого функцией ancestors"""
    result = menu_proxy.ancestors(obj)
    if result is None:
        return []
    return [value for value in result]

def get_children(menu_proxy, obj, lasy):
    u"""Корректировка значения, возвращаемого функцией children или force"""
    if lasy:
        result = menu_proxy.lasy_children(obj)
    else:
        result = menu_proxy.children(obj)
    if result is None:
        return []
    return [value for value in result]

def try_to_import(dictionary, key, exception_text):
    u"""Если значение key задано, пытаемся импортировать указанный объект"""
    value = dictionary.get(key, None)
    if not value is None:
        value = importpath(value, exception_text)
    dictionary[key] = value

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
        self.rules = {}
        
        for name, rule in getattr(conf.settings, 'MENU_PROXY_RULES', {}).iteritems():
            rule = rule.copy()
            if rule['method'] not in self.METHODS:
                raise ImproperlyConfigured('menuproxy does`t support method: %s', rule['method'])
            if 'proxy' not in rule:
                raise ImproperlyConfigured('menuproxy need proxy for %s rule' % name)

            rule['name'] = name
            rule['inside'] = rule.get('inside', None)
            try_to_import(rule, 'model', 'model class')
            try_to_import(rule, 'point', 'mount point function')
            if callable(rule['point']):
                rule['point'] = rule['point']()
            try_to_import(rule, 'object', 'mount object function')
            if callable(rule['object']):
                rule['object'] = rule['object']()
            try_to_import(rule, 'proxy', 'MenuProxy class')
            if callable(rule['proxy']):
                rule['proxy'] = rule['proxy'](**rule)
            if rule['method'] == 'instead' and rule['point'] is None:
                continue
            if rule['method'] == 'root':
                if self.root is not None:
                    raise ImproperlyConfigured('menuproxy does`t support more that one method "root"')
                rule['inside'] = None
                rule['point'] = None
                self.root = rule
            else:
                key = (rule['inside'], rule['point'])
                dictionary = getattr(self, rule['method'])
                if key in dictionary:
                    continue
                dictionary[key] = rule
            self.rules[name] = rule

        if self.root is None:
            raise ImproperlyConfigured('menuproxy must have rule with method "root"')

        self.top = get_children(self.root['proxy'], self.root['object'], False)
        
        if getattr(conf.settings, 'MENU_PROXY_FRONT_PAGED', True) and self.top:
            self.front_page = self.top[0]
            self.front_name = self.root['name']
        else:
            self.front_page = None
            self.front_name = None


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
    
    def __init__(self, name=None, obj=None):
        self.settings = get_settings()
        if name == None:
            name = self.settings.root['name']
        if isinstance(obj, MenuItem):
            obj = obj.obj
        self.source = []
        while (name, obj) in self.settings.instead:
            self.source.append((name, obj))
            instead = self.settings.instead[name, obj]
            name = instead['name']
            obj = instead['object']
        self.name = name
        self.obj = obj
        self.front_paged_ancestors = False
        
    def title(self):
        u"""Возвращает заголовок элемента меню"""
        if hasattr(self, '_title'):
            return getattr(self, '_title')
        title = get_title(self.settings.rules[self.name]['proxy'], self.obj)
        setattr(self, '_title', title)
        return title
            
    def url(self):
        u"""Возвращает url элемента меню"""
        if hasattr(self, '_url'):
            return getattr(self, '_url')
        url = get_url(self.settings.rules[self.name]['proxy'], self.obj)
        setattr(self, '_url', url)
        return url

    def ancestors(self):
        u"""Возвращает список родительских элементов меню, начиная с верхнего уровня"""
        if hasattr(self, '_ancestors'):
            return getattr(self, '_ancestors')
        
        ancestors = []
        name = self.name
        obj = self.obj
        while True:
            until = self.settings.rules[name]['object']
            items = get_ancestors(self.settings.rules[name]['proxy'], obj)
            items.reverse()
            for item in items:
                ancestors.insert(0, MenuItem(name, item))
                if item == until:
                    break
            method = self.settings.rules[name]['method']
            if method == 'root':
                break
            obj = self.settings.rules[name]['point']
            name = self.settings.rules[name]['inside']
            if method != 'instead':
                ancestors.insert(0, MenuItem(name, obj))
            
        if self.settings.front_page is not None:
            if not ancestors or ancestors[0].obj != self.settings.front_page:
                if (self.settings.front_name, self.settings.front_page) != (self.name, self.obj):
                    self.front_paged_ancestors = True
                    ancestors.insert(0, MenuItem(self.settings.root['name'], self.settings.front_page))
        setattr(self, '_ancestors', ancestors)
        return ancestors
    
    def ancestors_for_menu(self):
        ancestors = self.ancestors()
        if self.front_paged_ancestors:
            ancestors = ancestors[1:]
        else:
            ancestors = ancestors[:]
        ancestors.append(self)
        return ancestors

    def children(self, lasy):
        u"""Возвращает список дочерних элементов меню"""
        if hasattr(self, '_children'):
            return getattr(self, '_children')
        
        key = (self.name, self.obj)
        prepend = self.settings.prepend
        append = self.settings.append
        children = []
        if key in prepend:
            children += [
                MenuItem(prepend[key]['name'], item) for item in get_children(
                    prepend[key]['proxy'], prepend[key]['object'], lasy)
            ]
        children += [
            MenuItem(self.name, item) for item in get_children(
                self.settings.rules[self.name]['proxy'], self.obj, lasy)
        ]
        if key in append:
            children += [
                MenuItem(append[key]['name'], item) for item in get_children(
                    append[key]['proxy'], append[key]['object'], lasy)
            ]

        setattr(self, '_children', children)
        return children
