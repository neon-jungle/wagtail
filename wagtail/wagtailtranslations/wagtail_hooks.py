from django.conf.urls import include, url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import BaseDropdownMenuButton, Button
from wagtail.wagtailcore import hooks

from . import admin_urls
from .models import Language


class LanguageDropdown(BaseDropdownMenuButton):
    def __init__(self, page, **kwargs):
        self.page = page
        super(LanguageDropdown, self).__init__(
            label=_('Translations'), attrs={'target': '_blank'},
            **kwargs)

    def get_buttons_in_dropdown(self):
        url_params = {'app_label': self.page.specific_class._meta.app_label,
                      'model_name': self.page.specific_class._meta.model_name,
                      'pk': self.page.pk}
        for i, language in enumerate(Language.objects.all()):
            url_params['language'] = language.code
            url = reverse('wagtailtranslations:translate', kwargs=url_params)
            yield Button(language.name, url, priority=i)


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False):
    print("Woo")
    yield LanguageDropdown(page, priority=50)
    print("After")


@hooks.register('register_admin_urls')
def translation_urls():
    return [url('^translations/', include(admin_urls, namespace='wagtailtranslations', app_name='wagtailtranslations'))]
