from __future__ import absolute_import, unicode_literals

from django.utils.encoding import force_text

from wagtail.utils.widgets import safe_json
from wagtail.wagtailadmin.widgets import BaseAdminChooser


class AdminSnippetChooser(BaseAdminChooser):
    template = 'wagtailsnippets/widgets/snippet_chooser.html'
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        super(AdminSnippetChooser, self).__init__(**kwargs)
        if content_type is not None:
            self.target_content_type = content_type
        self.model = self.target_content_type.model_class()
        self.snippet_type_name = force_text(self.model._meta.verbose_name)

    def render(self, name, value, attrs=None, extra_context={}):
        item = self.model.objects.get(pk=value) if value else None
        context = {
            'item': item,
            'snippet_type_name': self.snippet_type_name,
            'snippet_app_model': safe_json('{app}/{model}'.format(
                app=self.model._meta.app_label,
                model=self.model._meta.model_name)),
        }
        context.update(extra_context)
        return super(AdminSnippetChooser, self).render(name, value, attrs, context)
