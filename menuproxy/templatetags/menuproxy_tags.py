# -*- coding: utf-8 -*-

from django import template
from django.http import HttpRequest
from django.template.loader import render_to_string

from menuproxy.utils import *

register = template.Library()

def get_value(string, context):
    if string is None:
        return None
    try:
        return template.Variable(string).resolve(context)
    except template.VariableDoesNotExist:
        return None

class CurrentNode(template.Node):
    def __init__(self, rule=None, obj=None):
        self.rule = rule
        self.obj = obj
    
    def render(self, context):
        rule = get_value(self.rule, context)
        obj = get_value(self.obj, context)
        if rule is None:
            context['current_menuproxy'] = None
        else:
            context['current_menuproxy'] = MenuItem(rule, obj)
        return ''

@register.tag
def current_menu_item(parser, token):
    u"""Устанавливаем текущий элемент в меню"""
    splited = token.split_contents()
    if len(splited) > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 2 arguments: rule, object" % splited[0]
    return CurrentNode(*splited[1:])


class MenuNode(template.Node):
    def __init__(self, tag_name, rule=None, obj=None):
        self.mode = tag_name.split('_')[1]
        self.rule = rule
        self.obj = obj
        
    def render(self, context):
        rule = get_value(self.rule, context)
        obj = get_value(self.obj, context)
        target = MenuItem(rule, obj)

        current = context.get('current_menuproxy', None)
        if current is not None:
            keys = [(ancestor.name, ancestor.obj)
                for ancestor in current.ancestors_for_menu()]
        else:
            keys = []
            

        if self.mode == 'auto' and target.obj is not None:
            lasy = (target.name, target.obj) not in keys
        else:
            lasy = False

        children = target.children(lasy)
        for child in children:
            if (child.name, child.obj) in keys:
                child.active = True
            if current is not None and (child.name, child.obj) == (current.name, current.obj):
                child.current = True

        return render_to_string('menuproxy/%s_menu.html' % self.mode, {
            'children': children,
            'current_menuproxy': current,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


def show_menu(parser, token):
    u"""Отображаем меню, начиная с указанного элемента"""
    splited = token.split_contents()
    if len(splited) > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 3 arguments: rule, obj" % splited[0]
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
        context['pop_breadcrumb'] = context.get('pop_breadcrumb', 0) + 1
        return u''


@register.tag
def pop_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) != 1:
        raise template.TemplateSyntaxError, "%r tag requires zero arguments" % splited[0]
    return PopNode()


class BreadCrumbNode(template.Node):
    def __init__(self, between_char='" →"'):
        self.between_char = between_char
        
    def render(self, context):
        between_char = get_value(self.between_char, context)
        
        current = context.get('current_menuproxy', None)
        if current is not None:
            ancestors = current.ancestors()
        else:
            ancestors = []
    
        breadcrumbs = ancestors
        if 'pop_breadcrumb' in context:
            breadcrumbs = breadcrumbs[:-context['pop_breadcrumb']]

        breadcrumbs = context.get('insert_breadcrumb', []) + \
            breadcrumbs + context.get('append_breadcrumb', [])

        return render_to_string('menuproxy/breadcrumb.html', {
            'breadcrumbs': breadcrumbs,
            'breadcrumb_between_char': between_char,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


@register.tag
def show_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) > 4:
        raise template.TemplateSyntaxError, "%r tag requires maximum 2 arguments: setting current and between_char" % splited[0]
    return BreadCrumbNode(*splited)
