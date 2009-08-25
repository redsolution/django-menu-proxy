# -*- coding: utf-8 -*-

from django import template
from django.http import HttpRequest
from django.template.loader import render_to_string

from menuproxy.utils import *

register = template.Library()

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
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


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
        }, context_instance=template.RequestContext(context.get('request', HttpRequest())))


@register.tag
def show_breadcrumbs(parser, token):
    splited = token.split_contents()
    if len(splited) > 3:
        raise template.TemplateSyntaxError, "%r tag requires maximum 2 arguments: current and between_char" % splited[0]
    return BreadCrumbNode(*splited)
