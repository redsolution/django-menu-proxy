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

def get_ancestors(menu_proxy, object):
    """Correct value returned by menu_proxy.ancestors function"""
    result = menu_proxy.ancestors(object)
    if result is None:
        return []
    return [value for value in result]

def get_children(menu_proxy, object, lasy):
    """
    Call ``children`` or ``lasy_children`` function for ``menu_proxy``.
    Pass to it ``object``.
    Correct result.
    """
    if lasy:
        result = menu_proxy.lasy_children(object)
    else:
        result = menu_proxy.children(object)
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
        model=DoesNotDefined, point=DoesNotDefined, object=DoesNotDefined, 
        point_function=DoesNotDefined, object_function=DoesNotDefined, **other):

        self.name = name
        self.method = method
        assert self.method in METHODS, 'menuproxy does`t support method: %s' % self.method
        self.inside = inside
        self.model = try_to_import(model, 'model class')
        self.point = try_to_import(point, 'mount point')
        if callable(self.point) and self.point is not DoesNotDefined:
            self.point = self.point()
        if self.point is DoesNotDefined:
            self.point_function = try_to_import(point_function, 'mount point function')
        else:
            self.point_function = DoesNotDefined
        self.object = try_to_import(object, 'mount object')
        if callable(self.object) and self.object is not DoesNotDefined:
            self.object = self.object()
        if self.object is DoesNotDefined:
            self.object_function = try_to_import(object_function, 'mount object function')
        else:
            self.object_function = DoesNotDefined
        self.proxy = try_to_import(proxy, 'MenuProxy class')
        other.update(self.__dict__)
        if callable(self.proxy) and self.proxy is not DoesNotDefined:
            self.proxy = self.proxy(**other)
        self.rules = rules
        self.sequence = []
        
    def _get_point(self, object, forward):
        if self.point is not DoesNotDefined:
            return self.point
        elif self.point_function is not DoesNotDefined:
            return self.point_function(object, forward)
        else:
            return DoesNotDefined

    def _get_object(self, object, forward):
        if self.object is not DoesNotDefined:
            return self.object
        elif self.object_function is not DoesNotDefined:
            return self.object_function(object, forward)
        else:
            return DoesNotDefined

    def forward_point(self, object):
        return self._get_point(object, True)

    def backward_point(self, object):
        return self._get_point(object, False)

    def forward_object(self, object):
        return self._get_object(object, True)

    def backward_object(self, object):
        return self._get_object(object, False)


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
                    point = rule.forward_point(object)
                    if point is DoesNotDefined or point == object:
                        self.name, self.object =  rule.name, rule.forward_object(object)
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
            items = get_ancestors(self.rules[name].proxy, object)
            until = self.rules[name].backward_object(object)
            items.reverse()
            for item in items:
                ancestors.insert(0, MenuItem(name, item))
                if item == until:
                    break
            method, object, name = self.rules[name].method, self.rules[name].backward_point(object), self.rules[name].inside
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

    def children(self, lasy=False):
        """Returns children for object"""
        if lasy:
            field_name = '_children_lasy'
        else:
            field_name = '_children'
        if hasattr(self, field_name):
            return getattr(self, field_name)
        
        children = []
        for rule in self.rules[self.name].sequence:
            point = rule.forward_point(self.object)
            if rule.name == self.name:
                children += [MenuItem(self.name, item) for item in get_children(
                    self.rules[self.name].proxy, self.object, lasy)
                ]
            elif point is DoesNotDefined or point == self.object:
                object = rule.forward_object(self.object)
                if rule.method == 'insert' and not lasy:
                    children += [MenuItem(rule.name, object)]
                elif rule.method == 'children':
                    children += [MenuItem(rule.name, item) for item in get_children(
                        rule.proxy, object, lasy)
                    ]
        setattr(self, field_name, children)
        return children
