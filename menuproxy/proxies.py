# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from menuproxy.utils import DoesNotDefined

class MenuProxy(object):
    u"""Базовый класс, описывающий метод получения данных из модели для построения меню"""

    def __init__(self, model=None, children_filter={}, children_exclude={},
        ancestors_filter={}, ancestors_exclude={}, **other):
        self.model = model
        self.children_filter = children_filter
        self.children_exclude = children_exclude
        self.ancestors_filter = ancestors_filter
        self.ancestors_exclude = ancestors_exclude

    def title(self, object):
        u"""Возвращает заголовок элемента"""
        assert object is not DoesNotDefined, DoesNotDefined
        if object is None:
            return None
        if not hasattr(object, 'title'):
            return unicode(object)
        if callable(object.title):
            return object.title()
        else:
            return object.title

    def url(self, object):
        u"""Возвращает url элемента"""
        assert object is not DoesNotDefined, DoesNotDefined
        if object is None:
            return None
        return object.get_absolute_url()

    def ancestors(self, object):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        if object is None or object is DoesNotDefined:
            return None
        return object.get_ancestors().filter(**self.ancestors_filter).exclude(**self.ancestors_exclude)

    def children(self, object):
        u"""Возвращает список дочерних элементов.
        Если object == None возвращает список элементов верхнего уровня"""
        if object is DoesNotDefined:
            object = None
        return self.model.objects.filter(parent=object).filter(**self.children_filter).exclude(**self.children_exclude)

    def lasy_children(self, object):
        u"""Возвращает список дочерних элементов,
        если объект не содержится в потомках выбранный элемент"""
        return None


class FlatProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из не древовидной модели. Отображает все элементы на верхнем уровне"""

    def ancestors(self, object):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, object):
        u"""Возвращает список дочерних элементов.
        Если object == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if object is None or object is DoesNotDefined:
            return self.model.objects.filter(**self.children_filter).exclude(**self.children_exclude)
        else:
            return None

class EmptyProxy(MenuProxy):
    u"""Класс, возвращающий пустой список дочерних и родительских элементов"""

    def ancestors(self, object):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, object):
        u"""Возвращает список дочерних элементов.
        Если object == None возвращает список элементов первого уровня"""
        return None

class StaticUrlProxy(MenuProxy):
    u"""Класс, возвращает указанный url"""

    def __init__(self, url_text=None, get_url=None,
        title_text=None, get_title=None, **other):

        self.url_text = url_text
        self.get_url = get_url
        self.title_text = title_text
        self.get_title = get_title

    def title(self, object):
        u"""Возвращает заголовок элемента"""
        if self.get_title is None:
            return self.title_text
        from importpath import importpath
        title = importpath(self.get_title)
        if callable(title):
            return title()
        else:
            return title

    def url(self, object):
        u"""Возвращает url элемента"""
        if self.get_url is None:
            return self.url_text
        from importpath import importpath
        url = importpath(self.get_url)
        if callable(url):
            return url()
        else:
            return url

    def ancestors(self, object):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, object):
        u"""Возвращает список дочерних элементов.
        Если object == None возвращает список элементов верхнего уровня"""
        return None

class ReverseProxy(StaticUrlProxy):
    u"""Класс, возвращает url по укананному именю view"""

    def __init__(self, viewname, title_text=None, get_title=None,
        args=None, kwargs=None, prefix=None, **other):

        self.viewname = viewname
        self.title_text = title_text
        self.get_title = get_title
        self.args = args
        self.kwargs = kwargs
        self.prefix = prefix

    def url(self, object):
        u"""Возвращает url элемента"""
        return reverse(viewname=self.viewname, args=self.args, kwargs=self.kwargs,
            prefix=self.prefix)
