# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

class MenuProxy(object):
    u"""Базовый класс, описывающий метод получения данных из модели для построения меню"""
    
    def __init__(self, *args, **kwargs):
        u"""Сохраняем аргументы переданные при создании объекта"""
        self.args = args
        self.kwargs = kwargs
    
    def title(self, model, obj):
        u"""Возвращает заголовок элемента"""
        return obj.title

    def url(self, model, obj):
        u"""Возвращает url элемента"""
        return obj.get_absolute_url()

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return obj.get_ancestors()

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов верхнего уровня.
        force == False только при построении разворачивающегося меню
        только для элементов, не содержащих в потомках выбранный элемент"""
        if force:
            return model.objects.filter(parent=obj)
        else:
            return None


class FlatProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из не древовидной модели. Отображаает все элементы на верхнем уровне"""

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if force:
            if obj is None:
                model.objects.all()
            else:
                return None
        else:
            return None

class EmptyProxy(MenuProxy):
    u"""Класс, возвращающий пустой список дочерних и родительских элементов"""

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        return None

class PagesProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из модели pages-cms"""

    def title(self, model, obj):
        u"""Возвращает заголовок элемента"""
        return obj.title()

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if force:
            return model.objects.filter(parent=obj).filter(status=1)
        else:
            return None

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return obj.get_ancestors().exclude(status=0)

class ReverseProxy(EmptyProxy):
    u"""Класс, описывающий метод получения данных из модели pages-cms"""
    
    def title(self, model, obj):
        u"""Возвращает заголовок элемента"""
        return u''

    def url(self, model, obj):
        u"""Возвращает url элемента"""
        return reverse(*self.args, **self.kwargs)


class FilterProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из модели и фильтровать список дочерних элементов"""

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if force:
            return model.objects.filter(parent=obj).filter(*self.args, **self.kwargs)
        else:
            return None
