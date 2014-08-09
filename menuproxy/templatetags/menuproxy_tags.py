# -*- coding: utf-8 -*-

from django import template
from django.http import HttpRequest
from django.template.loader import render_to_string

from menuproxy.utils import MenuItem, DoesNotDefined

register = template.Library()

def get_value(string, context, default=None):
    if string is None:
        return default
    try:
        result = template.Variable(string).resolve(context)
    except template.VariableDoesNotExist:
        return default
    if isinstance(result, DoesNotDefined):
        return DoesNotDefined
    return result


class MenuNode(template.Node):
    def __init__(self, tag_name, current_rule=None, current_obj=None, target_rule=None, target_obj=None, proxy=False):
        self.mode = tag_name.split('_')[1]
        self.current_rule = current_rule
        self.current_obj = current_obj
        self.target_rule = target_rule
        self.target_obj = target_obj
        self.proxy = proxy

    def render(self, context):
        if self.proxy:
            current = get_value(self.current_rule, context)
            target = get_value(self.current_obj, context, DoesNotDefined)
        else:
            current_rule = get_value(self.current_rule, context)
            current_obj = get_value(self.current_obj, context, DoesNotDefined)
            if current_rule is None:
                current = DoesNotDefined
            else:
                current = MenuItem(current_rule, current_obj)

            target_rule = get_value(self.target_rule, context)
            target_obj = get_value(self.target_obj, context, DoesNotDefined)
            target = MenuItem(target_rule, target_obj)

        if current is DoesNotDefined:
            keys = []
        else:
            keys = [(ancestor.name, ancestor.object)
                for ancestor in current.ancestors_for_menu()]

        if self.mode == 'auto':
            lasy = (target.name, target.object) not in keys
        else:
            lasy = False
        if target.name is None and target.object is DoesNotDefined:
            lasy = False

        children = target.children(lasy)
        for child in children:
            if (child.name, child.object) in keys:
                child.active = True
            if current is not None and current is not DoesNotDefined and (child.name, child.object) == (current.name, current.object):
                child.current = True

        menuproxy_level = context.get('menuproxy_level', -1) + 1
        return render_to_string('menuproxy/%s_menu.html' % self.mode, {
            'children': children,
            'current': current,
            'target': target,
            'menuproxy_level': menuproxy_level,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


def show_menu(parser, token):
    u"""Отображаем меню, начиная с указанного элемента"""
    splited = token.split_contents()
    if len(splited) - 1 > 4:
        raise template.TemplateSyntaxError, "%r tag requires maximum 4 arguments: current_rule current_obj target_rule target_obj" % splited[0]
    return MenuNode(*splited, **{'proxy': splited[0].endswith('for_proxy')})

register.tag('show_main_menu', show_menu)
register.tag('show_full_menu', show_menu)
register.tag('show_auto_menu', show_menu)
register.tag('show_main_menu_for_proxy', show_menu)
register.tag('show_full_menu_for_proxy', show_menu)
register.tag('show_auto_menu_for_proxy', show_menu)

class MakeBreadcrumbsNode(template.Node):
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
        context['menuproxy_breadcrumbs'] = ancestors
        return u''

@register.tag
def make_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 > 2:
        raise template.TemplateSyntaxError, "%r tag requires maximum  2 arguments: current_rule current_obj" % splited[0]
    return MakeBreadcrumbsNode(*splited[1:])

class ActionBreadcrumbNode(template.Node):
    def __init__(self, tag_name, title, url):
        self.tag_name = tag_name
        self.title = title
        self.url = url

    def render(self, context):
        title = get_value(self.title, context)
        url = get_value(self.url, context)
        item = [{'title': title, 'url': url}]
        menuproxy_breadcrumbs = context.get('menuproxy_breadcrumbs', [])
        if self.tag_name == 'append_breadcrumb':
            context['menuproxy_breadcrumbs'] = menuproxy_breadcrumbs + item
        elif self.tag_name == 'prepend_breadcrumb':
            context['menuproxy_breadcrumbs'] = item + menuproxy_breadcrumbs
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
        count = int(self.count)
        context['menuproxy_breadcrumbs'] = context.get('menuproxy_breadcrumbs', [])[:-count]
        return u''


@register.tag
def pop_breadcrumb(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 not in [0, 1]:
        raise template.TemplateSyntaxError, "%r tag requires zero or 1 argument: count" % splited[0]
    return PopBreadcrumbNode(*splited[1:])


class BreadcrumbsNode(template.Node):
    def __init__(self, current_rule=None, current_obj=None, between_char='" →"'):
        self.current_rule = current_rule
        self.current_obj = current_obj
        self.between_char = between_char

    def render(self, context):
        between_char = get_value(self.between_char, context)

        if 'menuproxy_breadcrumbs' in context:
            current = None
            ancestors = context['menuproxy_breadcrumbs']
        else:
            current_rule = get_value(self.current_rule, context)
            current_obj = get_value(self.current_obj, context)
            if current_rule is None:
                current = None
                ancestors = []
            else:
                current = MenuItem(current_rule, current_obj)
                ancestors = current.ancestors()

        return render_to_string('menuproxy/breadcrumbs.html', {
            'current': current,
            'breadcrumbs': ancestors,
            'breadcrumb_between_char': between_char,
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


@register.tag
def show_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) - 1 > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 3 arguments: current_rule current_obj between_char" % splited[0]
    return BreadcrumbsNode(*splited[1:])
