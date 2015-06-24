from __future__ import unicode_literals
from inspect import getargspec

from django.forms.utils import flatatt
from django.template import Node, TemplateSyntaxError
from django.template.base import parse_bits, Library, Node, TemplateSyntaxError, Context, TextNode
from django.template.loader import render_to_string, get_template
from django.template.loader_tags import BlockNode

from .config import NAMESPACE

class OptionalBlockNode(Node):

    @classmethod
    def parse_optional_blocks(cls, nodelist):
        name = 'block'
        end_tag = 'end' + name

        blocks = cls.OPTIONAL_BLOCKS
        parse_till = [end_tag] + list(blocks)
        
        final_nodelists = {}

        for node in nodelist:
            if isinstance(node, TextNode):
                if not node.s.isspace():
                    raise TemplateSyntaxError('Illegal content inside "%s" template tag' % cls.TAG_NAME)    
            elif not isinstance(node, BlockNode):
                raise TemplateSyntaxError('Illegal template tag inside "%s" template tag' % cls.TAG_NAME)
            elif node.name not in blocks:
                raise TemplateSyntaxError('Non-whitelisted block name inside "%s" template tag' % cls.TAG_NAME)
            else:
                final_nodelists[node.name] = node.nodelist

        return final_nodelists


class HeaderBlock(OptionalBlockNode):

    TAG_NAME = 'header'
    OPTIONAL_BLOCKS = ('left', 'right')

    TEMPLATE_NAME = 'wagtailadmin/ui/header.html'

    def __init__(self, section_nodelists={}):
        self.section_nodelists = section_nodelists

    def render(self, context):
        inner = {name: nodelist.render(context)
                for name, nodelist in self.section_nodelists.items()}

        return render_to_string(self.TEMPLATE_NAME, inner)

    @classmethod
    def handle(cls, parser, token):
        bits = token.split_contents()
        name = bits[0]

        inner_nodelists = parser.parse(['end' + name])
        parser.delete_first_token()

        full_nodelist = cls.parse_optional_blocks(inner_nodelists)

        return cls(full_nodelist)
