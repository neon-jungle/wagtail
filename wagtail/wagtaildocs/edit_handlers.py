from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminDocumentChooser


class BaseDocumentChooserPanel(BaseChooserPanel):
    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminDocumentChooser}


def DocumentChooserPanel(field_name):
    return type(str('_DocumentChooserPanel'), (BaseDocumentChooserPanel,), {
        'field_name': field_name,
    })
