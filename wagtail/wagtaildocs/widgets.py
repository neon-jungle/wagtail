from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.widgets import BaseAdminChooser
from .models import Document


class AdminDocumentChooser(BaseAdminChooser):
    template = 'wagtaildocs/widgets/document_chooser.html'

    def render(self, name, value, attrs=None, extra_context={}):
        document = Document.objects.get(pk=value) if value else None
        context = {'document': document}
        context.update(extra_context)
        return super(AdminDocumentChooser, self).render(name, value, attrs, context)
