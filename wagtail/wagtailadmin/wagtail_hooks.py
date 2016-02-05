from django.contrib.auth.models import Permission
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles.templatetags.staticfiles import static

from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem, settings_menu
from wagtail.wagtailadmin.search import SearchArea
from wagtail.wagtailcore import hooks

from .link_choosers import (
    EmailLinkChooser, ExternalLinkChooser, InternalLinkChooser)


class ExplorerMenuItem(MenuItem):
    class Media:
        js = [static('wagtailadmin/js/explorer-menu.js')]


@hooks.register('register_admin_menu_item')
def register_explorer_menu_item():
    return ExplorerMenuItem(
        _('Explorer'), urlresolvers.reverse('wagtailadmin_explore_root'),
        name='explorer',
        classnames='icon icon-folder-open-inverse dl-trigger',
        attrs={'data-explorer-menu-url': urlresolvers.reverse('wagtailadmin_explorer_nav')},
        order=100)


@hooks.register('register_admin_menu_item')
def register_settings_menu():
    return SubmenuMenuItem(
        _('Settings'), settings_menu, classnames='icon icon-cogs', order=10000)


@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin')


@hooks.register('register_admin_search_area')
def register_pages_search_area():
    return SearchArea(
        _('Pages'), urlresolvers.reverse('wagtailadmin_pages:search'),
        name='pages',
        classnames='icon icon-folder-open-inverse',
        order=100)


@hooks.register('register_link_chooser')
def register_internal_link_chooser():
    return InternalLinkChooser()


@hooks.register('register_link_chooser')
def register_external_link_chooser():
    return ExternalLinkChooser()


@hooks.register('register_link_chooser')
def register_email_link_chooser():
    return EmailLinkChooser()
