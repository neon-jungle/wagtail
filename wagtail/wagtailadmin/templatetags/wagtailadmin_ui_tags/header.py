from __future__ import unicode_literals
from inspect import getargspec

from django.forms.utils import flatatt
from django.template import Node, TemplateSyntaxError
from django.template.base import parse_bits, Library, Node, TemplateSyntaxError, Context, TextNode
from django.template.loader import render_to_string, get_template
from django.template.loader_tags import BlockNode

from .config import NAMESPACE
from .utils import WuiOptionalBlockNode


class HeaderBlock(WuiOptionalBlockNode):

    TAG_NAME = 'header'
    OPTIONAL_BLOCKS = ('search_form', 'before_buttons', 'buttons')

    def render_template(self, context, title, subtitle=None, icon=None):
        return render_to_string('wagtailadmin/ui/header.html', {
            'blocks': self.render_blocks(context),
            'title': title,
            'subtitle': subtitle,
            'icon': icon,
        })