# -*- coding: utf-8 -*-

from django import conf
from django.core.cache import cache
from importpath import importpath

METHODS = (
    'replace', # Указывает, что объект point следует заменить объектом object
    'insert', # Указывает, что к списку дочерних элементов inside-правила нужно добавить элемент object
    'children', # Указывает, что к списку дочерних элементов inside-правила нужно добавить дочерние элементы object-а 
)

def get_title(menu_proxy, object):
    """Correct value returned by menu_proxy.title function"""
    result = menu_proxy.title(object)
    if result is None:
        return u''
    return unicode(result)

def get_url(menu_proxy, object):
    """Correct value returned by menu_proxy.url function"""
    result = menu_proxy.url(object)
    if result is None:
        return u''
    return unicode(result)

def get_ancestors(menu_proxy, object, menu_item):
    """Correct value returned by menu_proxy.ancestors function"""
    result = menu_proxy.ancestors(object, menu_item)
    if result is None:
        return []
    return [value for value in result]

def get_children(menu_proxy, object, menu_item, lasy):
    """
    Call ``children`` or ``lasy_children`` function for ``menu_proxy``.
    Pass to it ``object`` and parent ``menu_item``.
    Correct result.
    """
    if lasy:
        result = menu_proxy.lasy_children(object, menu_item)
    else:
        result = menu_proxy.children(object, menu_item)
    if result is None:
        return []
    return [value for value in result]

class DoesNotDefined(object):
    """
    Class to indicate that value was not pressend in rule. 
    """
    pass

def try_to_import(value, exception_text):
    """
    If ``value`` is not None and is not DoesNotDefined
    then try to import specified by ``value`` path.
    """
    if value is not DoesNotDefined and value is not None:
        return importpath(value, exception_text)
    return value

def get_rules():
    """Return dictionary of rules with settings"""
    rules = cache.get('menuproxy.rules', None)
    if rules is not None:
        return rules

    rules = {}
    sequence = {None: []}
    
    def add_to_sequence(rule, value):
        if rule not in sequence:
            sequence[rule] = []
        sequence[rule].append(value)
        
    rules[None] = MenuRule(name=None, method='replace', proxy=None, rules=rules)
    for kwargs in getattr(conf.settings, 'MENU_PROXY_RULES', []):
        rule = MenuRule(rules=rules, **kwargs)
        rules[rule.name] = rule
        add_to_sequence(rule.name, rule.name)
        add_to_sequence(rule.inside, rule.name)

    for name, rule in rules.iteritems():
        rule.sequence = [rules[item] for item in sequence[name]]
    
    cache.set('menuproxy.rules', rules)
    return rules

def get_front_page(rules):
    """If MENU_PROXY_FRONT_PAGED is True and there is front page return MenuItem for it"""
    front_page = cache.get('menuproxy.front_page', DoesNotDefined)
    if front_page is not DoesNotDefined:
        return front_page

    front_page = None
    if getattr(conf.settings, 'MENU_PROXY_FRONT_PAGED', True):
        root = MenuItem(None, DoesNotDefined)
        children = root.children(False)
        if children:
            front_page = children[0]

    cache.set('menuproxy.front_page', front_page)
    return front_page

class MenuRule(object):
    """Rule"""
    
    def __init__(self, name, method, proxy, rules, inside=None,
        model=DoesNotDefined, point=DoesNotDefined, object=DoesNotDefined, **other):

        self.name = name
        self.method = method
        assert self.method in METHODS, 'menuproxy does`t support method: %s' % self.method
        self.inside = inside
        self.model = try_to_import(model, 'model class')
        self.point = try_to_import(point, 'mount point function')
        if callable(self.point) and self.point is not DoesNotDefined:
            self.point = self.point()
        self.object = try_to_import(object, 'mount object function')
        if callable(self.object) and self.object is not DoesNotDefined:
            self.object = self.object()
        self.proxy = try_to_import(proxy, 'MenuProxy class')
        other.update(self.__dict__)
        if callable(self.proxy) and self.proxy is not DoesNotDefined:
            self.proxy = self.proxy(**other)
        self.rules = rules
        self.sequence = []


class MenuItem(object):
    """Objects of this class will be send to templates. Class provide to walk through nested rules"""

    active = False
    current = False

    def __init__(self, name=None, object=None):
        if isinstance(object, MenuItem):
            self.rules = object.rules
            self.name, self.object = object.name, object.object
        else:
            self.rules = get_rules()
            for rule in self.rules[name].sequence:
                if rule.name != name and rule.method == 'replace':
                    if rule.point is DoesNotDefined or rule.point == object:
                        self.name, self.object =  rule.name, rule.object
                        break
            else:
                self.name, self.object =  name, object
        self.front_paged_ancestors = False
        
    def title(self):
        """Returns title for object"""
        if hasattr(self, '_title'):
            return getattr(self, '_title')
        title = get_title(self.rules[self.name].proxy, self.object)
        setattr(self, '_title', title)
        return title
            
    def url(self):
        """Returns url for object"""
        if hasattr(self, '_url'):
            return getattr(self, '_url')
        url = get_url(self.rules[self.name].proxy, self.object)
        setattr(self, '_url', url)
        return url

    def ancestors(self):
        """Returns ancestors for object, started from top level"""
        if hasattr(self, '_ancestors'):
            return getattr(self, '_ancestors')
        
        ancestors = []
        name = self.name
        object = self.object
        while True:
            until = self.rules[name].object
            items = get_ancestors(self.rules[name].proxy, object, self)
            items.reverse()
            for item in items:
                ancestors.insert(0, MenuItem(name, item))
                if item == until:
                    break
            method, object, name = self.rules[name].method, self.rules[name].point, self.rules[name].inside
            if name is None:
                break
            if method != 'replace':
                ancestors.insert(0, MenuItem(name, object))
        
        front_page = get_front_page(self.rules)
        if front_page is not None:
            if not ancestors or ancestors[0].object != front_page.object:
                if (front_page.name, front_page.object) != (self.name, self.object):
                    self.front_paged_ancestors = True
                    ancestors.insert(0, front_page)
        setattr(self, '_ancestors', ancestors)
        return ancestors
    
    def ancestors_for_menu(self):
        """
        Returns ancestors for show_menu tags.
        Ancestors will not contain front page and will contain object itself.
        """ 
        ancestors = self.ancestors()
        if self.front_paged_ancestors:
            ancestors = ancestors[1:]
        else:
            ancestors = ancestors[:]
        ancestors.append(self)
        return ancestors

    def children(self, lasy):
        """Returns children for object"""
        if hasattr(self, '_children'):
            return getattr(self, '_children')
        
        children = []
        for rule in self.rules[self.name].sequence:
            if rule.name == self.name:
                children += [MenuItem(self.name, item) for item in get_children(
                    self.rules[self.name].proxy, self.object, self, lasy)
                ]
            elif rule.point is DoesNotDefined or rule.point == self.object:
                if rule.method == 'insert' and not lasy:
                    children += [MenuItem(rule.name, rule.object)]
                elif rule.method == 'children':
                    children += [MenuItem(rule.name, item) for item in get_children(
                        rule.proxy, rule.object, self, lasy)
                    ]
        setattr(self, '_children', children)
        return children
