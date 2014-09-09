from __future__ import absolute_import, unicode_literals

import json

from django.core.urlresolvers import reverse
from django.forms import widgets

from wagtail.utils.widgets import WidgetWithScript

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


class AdminPageChooser(WidgetWithScript, widgets.Input):
    input_type = 'hidden'
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        print 'Created admin page chooser for content type', content_type.model_class()
        super(AdminPageChooser, self).__init__(**kwargs)
        if content_type is not None:
            self.target_content_type = content_type

    def render_js_init(self, id_, name, value):
        page = value
        parent = page.get_parent() if page else None
        content_type = self.target_content_type

        return "createPageChooser({id}, {content_type}, {parent});".format(
            id=json.dumps(id_),
            content_type=json.dumps('{app}.{model}'.format(
                app=content_type.app_label,
                model=content_type.model)),
            parent=json.dumps(parent.id if parent else None))
