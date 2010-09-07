from redsolutioncms.make import BaseMake
from redsolutioncms.models import CMSSettings
from django.template.loader import render_to_string

class Make(BaseMake):
    def premake(self):
        super(Make, self).premake()
        cms_settings = CMSSettings.objects.get_settings()
        cms_settings.top_blocks.create(html=
            render_to_string('menuproxy/redsolutioncms/top.html'))
        cms_settings.left_blocks.create(html=
            render_to_string('menuproxy/redsolutioncms/left.html'))
        cms_settings.center_blocks.create(html=
            render_to_string('menuproxy/redsolutioncms/center.html'))
        cms_settings.right_blocks.create(html=
            render_to_string('menuproxy/redsolutioncms/right.html'))

    def make(self):
        super(Make, self).make()
        cms_settings = CMSSettings.objects.get_settings()
        cms_settings.render_to('settings.py', 'menuproxy/redsolutioncms/settings.pyt', {
        })

make = Make()