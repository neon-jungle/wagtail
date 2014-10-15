from __future__ import absolute_import, unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text

from wagtail.wagtailadmin.edit_handlers import BaseChooserPanel
from .widgets import AdminSnippetChooser


class BaseSnippetChooserPanel(BaseChooserPanel):
    _content_type = None

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: AdminSnippetChooser(
            content_type=cls.content_type())}

    @classmethod
    def content_type(cls):
        if cls._content_type is None:
            # TODO: infer the content type by introspection on the foreign key rather than having to pass it explicitly
            cls._content_type = ContentType.objects.get_for_model(cls.snippet_type)

        return cls._content_type


def SnippetChooserPanel(field_name, snippet_type):
    return type(str('_SnippetChooserPanel'), (BaseSnippetChooserPanel,), {
        'field_name': field_name,
        'snippet_type_name': force_text(snippet_type._meta.verbose_name),
        'snippet_type': snippet_type,
    })
