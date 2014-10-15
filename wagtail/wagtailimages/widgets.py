from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.widgets import BaseAdminChooser
from .models import Image


class AdminImageChooser(BaseAdminChooser):
    template = 'wagtailimages/widgets/image_chooser.html'

    def render(self, name, value, attrs=None, extra_context={}):
        image = Image.objects.get(pk=value) if value else None
        context = {'image': image}
        context.update(extra_context)
        return super(AdminImageChooser, self).render(name, value, attrs, context)
