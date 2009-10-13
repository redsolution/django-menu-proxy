# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

class MenuProxy(object):
    u"""Базовый класс, описывающий метод получения данных из модели для построения меню"""
    
    def __init__(self, model=None, children_filter=None, children_exclude=None,
        ancestors_filter=None, ancestors_exclude=None, **kwargs):
        self.model = model
        self.filter = filter
        self.exclude = exclude
    
    def title(self, obj):
        u"""Возвращает заголовок элемента"""
        if callable(obj.title):
            return obj.title()
        else:
            return obj.title

    def url(self, obj):
        u"""Возвращает url элемента"""
        return obj.get_absolute_url()

    def ancestors(self, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return obj.get_ancestors().filter(self.ancestors_filter).exclude(self.ancestors_exclude)

    def children(self, obj):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов верхнего уровня"""
        return model.objects.filter(parent=obj).filter(self.children_filter).exclude(self.children_exclude)
    
    def force_children(self, obj):
        u"""Возвращает список дочерних элементов,
        если объект не содержится в потомках выбранный элемент"""
        return None


class FlatProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из не древовидной модели. Отображает все элементы на верхнем уровне"""

    def ancestors(self, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, obj):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if obj is None:
            model.objects.filter(self.filter).filter(self.children_filter).exclude(self.children_exclude)
        else:
            return None

class EmptyProxy(MenuProxy):
    u"""Класс, возвращающий пустой список дочерних и родительских элементов"""

    def ancestors(self, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, obj):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня"""
        return None

class ReverseProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из модели pages-cms"""

    def __init__(self, args=[], kwargs={}, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def title(self, obj):
        u"""Возвращает заголовок элемента"""
        return u''

    def url(self, model, obj):
        u"""Возвращает url элемента"""
        return reverse(*self.args, **self.kwargs)

    def ancestors(self, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, obj):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов верхнего уровня"""
        return None
