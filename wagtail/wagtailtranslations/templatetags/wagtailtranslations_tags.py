from django.template import Library
from wagtail.wagtailtranslations.models import Language

register = Library()


@register.simple_tag(takes_context=True)
def get_languages(context):
    return Language.objects.active()
