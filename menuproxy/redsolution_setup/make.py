from redsolutioncms.make import BaseMake
from redsolutioncms.models import CMSSettings
from django.template.loader import render_to_string

class Make(BaseMake):
    def make(self):
        super(Make, self).make()
        cms_settings = CMSSettings.objects.get_settings()
        cms_settings.render_to('settings.py', 'menuproxy/redsolutioncms/settings.pyt', {
        })
        cms_settings.render_to(['..', 'templates', 'base_menuproxy.html'],
            'menuproxy/redsolutioncms/base_menuproxy.html', {
        }, 'w')
        cms_settings.base_template = 'base_menuproxy.html'
        cms_settings.save()

make = Make()
