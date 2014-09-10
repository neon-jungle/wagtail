from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminImageChooser


class BaseImageChooserPanel(BaseChooserPanel):
    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminImageChooser}


def ImageChooserPanel(field_name):
    return type(str('_ImageChooserPanel'), (BaseImageChooserPanel,), {
        'field_name': field_name,
    })
