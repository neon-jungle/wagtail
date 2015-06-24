from django.template.base import Library
from .button import Button
from .header import HeaderBlock

register = Library()

register.tag(Button.TAG_NAME, Button.handle)
register.tag(HeaderBlock.TAG_NAME, HeaderBlock.handle)
