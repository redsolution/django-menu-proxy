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


class MenuNode(template.Node):
    def __init__(self, tag_name, current_rule=None, current_obj=None, target_rule=None, target_obj=None):
        self.mode = tag_name.split('_')[1]
        self.current_rule = current_rule
        self.current_obj = current_obj
        self.target_rule = target_rule
        self.target_obj = target_obj
        
    def render(self, context):
        current_rule = get_value(self.current_rule, context)
        current_obj = get_value(self.current_obj, context)
        if current_rule is None:
            current = None
            keys = []
        else:
            current = MenuItem(current_rule, current_obj)
            keys = [(ancestor.name, ancestor.obj)
                for ancestor in current.ancestors_for_menu()]

        target_rule = get_value(self.target_rule, context)
        target_obj = get_value(self.target_obj, context)
        target = MenuItem(target_rule, target_obj)

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
            'current': current,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


def show_menu(parser, token):
    u"""Отображаем меню, начиная с указанного элемента"""
    splited = token.split_contents()
    if len(splited) - 1 not in [0, 2, 4]:
        raise template.TemplateSyntaxError, "%r tag requires 0, 2 or 4 arguments: [current_rule current_obj [target_rule target_obj]]" % splited[0]
    return MenuNode(*splited)
    
register.tag('show_main_menu', show_menu)
register.tag('show_full_menu', show_menu)
register.tag('show_auto_menu', show_menu)

class MakeBreadcrumbNode(template.Node):
    def __init__(self, current_rule=None, current_obj=None):
        self.current_rule = current_rule
        self.current_obj = current_obj

    def render(self, context):
        current_rule = get_value(self.current_rule, context)
        current_obj = get_value(self.current_obj, context)
        if current_rule is None:
            ancestors = []
        else:
            current = MenuItem(current_rule, current_obj)
            ancestors = current.ancestors()
        context['menuproxy_breadcrumb'] = ancestors
        return u''

@register.tag
def make_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 not in [0, 2]:
        raise template.TemplateSyntaxError, "%r tag requires 0 or 2 arguments: [current_rule current_obj]" % splited[0]
    return MakeBreadcrumbNode(*splited[1:])

class ActionBreadcrumbNode(template.Node):
    def __init__(self, tag_name, title, url):
        self.tag_name = tag_name
        self.title = title
        self.url = url

    def render(self, context):
        title = get_value(self.title)
        url = get_value(self.url)
        item = [{'title': title, 'url': url}]
        menuproxy_breadcrumb = context.get('menuproxy_breadcrumb', [])
        if self.tag_name == 'append_breadcrumb':
            context['menuproxy_breadcrumb'] = item + menuproxy_breadcrumb
        else:
            context['menuproxy_breadcrumb'] = menuproxy_breadcrumb + item
        return u''

def action_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) != 3:
        raise template.TemplateSyntaxError, "%r tag requires 2 arguments: title and url" % splited[0]
    return ActionBreadcrumbNode(*splited)
register.tag('prepend_breadcrumb', action_breadcrumb)
register.tag('append_breadcrumb', action_breadcrumb)


class PopBreadcrumbNode(template.Node):
    def __init__(self, count=1):
        self.count = count

    def render(self, context):
        count = get_value(self.count)
        context['menuproxy_breadcrumb'] = context.get('menuproxy_breadcrumb', [])[:-count]
        return u''


@register.tag
def pop_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 not in [0, 1]:
        raise template.TemplateSyntaxError, "%r tag requires zero or 1 argument: count" % splited[0]
    return PopNode(*splited[1:])


class BreadcrumbNode(template.Node):
    def __init__(self, current_rule=None, current_obj=None, between_char='" →"'):
        self.current_rule = current_rule
        self.current_obj = current_obj
        self.between_char = between_char

    def render(self, context):
        between_char = get_value(self.between_char, context)
        
        if 'menuproxy_breadcrumb' is context:
            ancestors = context['menuproxy_breadcrumb']
        else:
            current_rule = get_value(self.current_rule, context)
            current_obj = get_value(self.current_obj, context)
            if current_rule is None:
                ancestors = []
            else:
                current = MenuItem(current_rule, current_obj)
                ancestors = current.ancestors()

        return render_to_string('menuproxy/breadcrumb.html', {
            'breadcrumbs': ancestors,
            'breadcrumb_between_char': between_char,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


@register.tag
def show_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 not in [0, 2, 3]:
        raise template.TemplateSyntaxError, "%r tag requires 0, 2 or 3 arguments: [current_rule current_obj [between_char]]" % splited[0]
    return BreadcrumbNode(*splited[1:])
