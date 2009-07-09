# -*- coding: utf-8 -*-

from django import template
from django import conf
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

register = template.Library()

def import_item(path, error_text):
    u"""Импортирует по указанному пути. В случае ошибки генерируется исключение с указанным текстом"""
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        return getattr(__import__(module, {}, {}, ['']), attr)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing %s %s: "%s"' % (error_text, path, e))


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
            if setting['point'] == item['point']:
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
        title = self.proxy._title(self.model, self.obj)
        setattr(self, '_title', title)
        return title
            
    def url(self):
        u"""Возвращает url элемента меню"""
        if hasattr(self, '_url'):
            return getattr(self, '_url')
        url = self.proxy._url(self.model, self.obj)
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
                for item in proxy._ancestors(model, obj)] + ancestors
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
            for item in proxy._children(model, obj, force)]
        setattr(self, '_children', children)
        return children


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


class MenuNode(template.Node):
    def __init__(self, tag_name, current=None, target=None):
        self.mode = tag_name.split('_')[1]
        if current is None:
            self.current = None
        else:
            self.current = template.Variable(current)
        if target is None:
            self.target = None
        else:
            self.target = template.Variable(target)
        
    def render(self, context):
        settings = get_settings()

        if self.current is None:
            current = None
        else:
            try:
                current = self.current.resolve(context)
            except template.VariableDoesNotExist:
                current = None
        current = get_item(settings, current)
        ancestors = current.ancestors()
        ancestors.append(current)
        ancestors_as_objects = [ancestor.obj
            for ancestor in ancestors]

        if self.target is None:
            target = None
        else:
            try:
                target = self.target.resolve(context)
            except template.VariableDoesNotExist:
                target = None
        target = get_item(settings, target)
        
        if self.mode == 'auto' and target.obj is not None:
            if current.obj is None:
                force = False
            else:
                force = target.obj in ancestors_as_objects
        else:
            force = True
        children = target.children(force)
        for child in children:
            if child.obj in ancestors_as_objects:
                child.active = True
            if child.obj == current.obj:
                child.current = True

        return render_to_string('menuproxy/%s_menu.html' % self.mode, {
            'current': current,
            'children': children,
        }, context_instance=template.RequestContext(context['request']))


def show_menu(parser, token):
    splited = token.split_contents()
    if len(splited) > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 2 arguments: current and target" % splited[0]
    return MenuNode(*splited)
    
register.tag('show_main_menu', show_menu)
register.tag('show_full_menu', show_menu)
register.tag('show_auto_menu', show_menu)

class BreadcrumbAction(template.Node):
    def __init__(self, tag_name, title, url):
        self.tag_name = tag_name
        self.title = title
        self.url = url

    def render(self, context):
        title = template.Variable(self.title).resolve(context)
        url = template.Variable(self.url).resolve(context)
        item = [{'title': title, 'url': url}]
        value = context.get(self.tag_name, [])
        if self.tag_name == 'insert_breadcrumb':
            context[self.tag_name] = item + value
        else:
            context[self.tag_name] = value + item
        return u''

def action_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) == 3:
        tag_name, title, url = splited
        return BreadcrumbAction(tag_name, title, url)
    raise template.TemplateSyntaxError, "%r tag requires 2 arguments: title and url" % splited[0]
register.tag('insert_breadcrumb', action_breadcrumb)
register.tag('append_breadcrumb', action_breadcrumb)


class PopNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        context['pop_breadcrumb'] = True
        return u''


@register.tag
def pop_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) != 1:
        raise template.TemplateSyntaxError, "%r tag requires zero arguments" % splited[0]
    return PopNode()


class BreadCrumbNode(template.Node):
    def __init__(self, tag_name, current=None, between_char='" →"'):
        if current is None:
            self.current = None
        else:
            self.current = template.Variable(current)
        self.between_char = template.Variable(between_char)
        
    def render(self, context):
        settings = get_settings()
        if self.current is None:
            current = None
        else:
            try:
                current = self.current.resolve(context)
            except template.VariableDoesNotExist:
                current = None
        current = get_item(settings, current)
        ancestors = current.ancestors()
        if current.obj is not None:
            ancestors.append(current)
    
        try:
            between_char = self.between_char.resolve(context)
        except template.VariableDoesNotExist:
            between_char = None

        breadcrumbs = context.get('insert_breadcrumb', []) + \
            ancestors + context.get('append_breadcrumb', [])

        if context.get('pop_breadcrumb', False):
            breadcrumbs = breadcrumbs[:-1]

        return render_to_string('menuproxy/breadcrumb.html', {
            'breadcrumbs': breadcrumbs,
            'breadcrumb_between_char': between_char,
        }, context_instance=template.RequestContext(context['request']))


@register.tag
def show_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 2 arguments: current and between_char" % splited[0]
    return BreadCrumbNode(*splited)
