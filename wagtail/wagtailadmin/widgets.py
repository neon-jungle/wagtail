from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from wagtail.utils.widgets import WidgetWithScript, safe_json

from taggit.forms import TagWidget


class AdminDateInput(WidgetWithScript, widgets.DateInput):
    def render_js_init(self, id_, name, value):
        return 'initDateChooser({});'.format(json.dumps(id_))


class AdminTimeInput(WidgetWithScript, widgets.TimeInput):
    def render_js_init(self, id_, name, value):
        return 'initTimeChooser({});'.format(json.dumps(id_))


class AdminDateTimeInput(WidgetWithScript, widgets.DateTimeInput):
    def render_js_init(self, id_, name, value):
        return 'initDateTimeChooser({});'.format(json.dumps(id_))


class AdminTagWidget(WidgetWithScript, TagWidget):
    def render_js_init(self, id_, name, value):
        return "initTagField({0}, {1});".format(
            json.dumps(id_),
            json.dumps(reverse('wagtailadmin_tag_autocomplete')))


class BaseAdminChooser(widgets.Input):
    input_type = 'hidden'
    template = 'wagtailadmin/widgets/chooser.html'

    def render(self, name, value, attrs=None, extra_context={}):
        widget = super(BaseAdminChooser, self).render(name, value, attrs)
        attrs = self.build_attrs(attrs)
        context = {
            'id': attrs.get('id', None),
            'id_js': safe_json(attrs.get('id', None)),
            'widget': widget,
            'is_chosen': value is not None,
        }
        context.update(extra_context)
        return mark_safe(render_to_string(self.template, context))


class AdminPageChooser(BaseAdminChooser):
    template = 'wagtailadmin/widgets/page_chooser.html'
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        print 'Created admin page chooser for content type', content_type.model_class()
        super(AdminPageChooser, self).__init__(**kwargs)
        if content_type is not None:
            self.target_content_type = content_type

    def render(self, name, value, attrs=None, extra_context={}):
        content_type = self.target_content_type
        Model = content_type.model_class()

        if value:
            page = Model.objects.get(pk=value)
            parent = page.get_parent()
        else:
            page, parent = None, None

        context = {
            'page': page,
            'content_type': safe_json('{0}.{1}'.format(
                Model._meta.app_label, Model._meta.model_name)),
            'parent': safe_json(parent.id if parent else None),
        }
        context.update(extra_context)
        return super(AdminPageChooser, self).render(name, value, attrs, context)
