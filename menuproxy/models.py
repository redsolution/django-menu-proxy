# -*- coding: utf-8 -*-

class MenuProxy(object):
    u"""Базовый класс, описывающий метод получения данных из модели для построения меню"""
    
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


class ShowableMenuProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из модели с полем show (отображать элемент или нет)"""

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if force:
            return model.objects.filter(parent=obj).filter(show=True)
        else:
            return None


class FlatMenuProxy(MenuProxy):
    u"""Класс, описывающий метод получения данных из не древовидной модели. Отображаает все элементы на верхнем уровне"""

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        return None

    def children(self, model, obj, force):
        u"""Возвращает список дочерних элементов.
        Если obj == None возвращает список элементов первого уровня.
        force == False только при построении разворачивающегося меню и
        только для элементов, не содержащих в потомках выбранный элемент"""
        if obj is None:
            model.objects.all()
        else:
            return None

class EmptyMenuProxy(MenuProxy):
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

class PagesMenuProxy(MenuProxy):
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


class PagesMenuProxyWithFrontPage(PagesMenuProxy):
    u"""Класс, описывающий метод получения данных из модели pages-cms"""
    
    def front_page(self, model, obj):
        u"""Возвращает список из корневого элемента, если он существует и нужен в breadcrumb-е"""
        from django.core.cache import cache
        front_page = cache.get('PagesMenuProxyWithFrontPage.front_page.%s' % model, False)
        if front_page == False:
            navigation = model.objects.navigation()
            try:
                front_page = navigation[0]
            except IndexError:
                front_page = None
            cache.set('PagesMenuProxyWithFrontPage.front_page.%s' % model, front_page)
        return front_page

    def url(self, model, obj):
        u"""Возвращает url элемента"""
        if self.front_page(model, obj) == obj:
            return '/'
        else:
            return obj.get_absolute_url()

    def ancestors(self, model, obj):
        u"""Возвращает список родительских элементов, начиная с верхнего уровня"""
        result = [item for item in obj.get_ancestors().exclude(status=0)]
        front_page = self.front_page(model, obj)
        if front_page is not None and front_page != obj and (not result or result[0] != front_page):
            result.insert(0, front_page)
        return result 


def catalog_to_pages():
    u"""Возвращает элемент pages к которому будет подключен каталог"""
    from pages.utils import get_page_from_slug
    return get_page_from_slug('catalog')


def news_to_pages():
    u"""Возвращает элемент pages к которому будет подключены новости"""
    from pages.utils import get_page_from_slug
    return get_page_from_slug('news')
