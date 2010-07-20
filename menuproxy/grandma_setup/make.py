from grandma.make import BaseMake
from grandma.models import GrandmaSettings
from django.template.loader import render_to_string

class Make(BaseMake):
    def premake(self):
        super(Make, self).premake()
        grandma_settings = GrandmaSettings.objects.get_settings()
        grandma_settings.top_blocks.create(html=
            render_to_string('menuproxy/grandma/top.html'))
        grandma_settings.left_blocks.create(html=
            render_to_string('menuproxy/grandma/left.html'))
        grandma_settings.center_blocks.create(html=
            render_to_string('menuproxy/grandma/center.html'))
        grandma_settings.right_blocks.create(html=
            render_to_string('menuproxy/grandma/right.html'))

    def make(self):
        super(Make, self).make()
        grandma_settings = GrandmaSettings.objects.get_settings()
        grandma_settings.render_to('settings.py', 'menuproxy/grandma/settings.py', {
        })
