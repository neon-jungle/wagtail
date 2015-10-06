from __future__ import absolute_import, unicode_literals

import sys
import warnings
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import six
from django.utils.text import slugify

from wagtail.wagtailcore.models import Page


class WagtailTestUtils(object):
    def login(self):
        # Create a user
        user = get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')

        # Login
        self.client.login(username='test', password='password')

        return user

    def assertRegex(self, *args, **kwargs):
        six.assertRegex(self, *args, **kwargs)

    @staticmethod
    @contextmanager
    def ignore_deprecation_warnings():
        with warnings.catch_warnings(record=True) as warning_list:  # catch all warnings
            yield

        # rethrow all warnings that were not DeprecationWarnings or PendingDeprecationWarnings
        for w in warning_list:
            if not issubclass(w.category, (DeprecationWarning, PendingDeprecationWarning)):
                warnings.showwarning(
                    message=w.message,
                    category=w.category,
                    filename=w.filename,
                    lineno=w.lineno,
                    file=w.file,
                    line=w.line
                )

    # borrowed from https://github.com/django/django/commit/9f427617e4559012e1c2fd8fce46cbe225d8515d
    @staticmethod
    def reset_warning_registry():
        """
        Clear warning registry for all modules. This is required in some tests
        because of a bug in Python that prevents warnings.simplefilter("always")
        from always making warnings appear: http://bugs.python.org/issue4180

        The bug was fixed in Python 3.4.2.
        """
        key = "__warningregistry__"
        for mod in list(sys.modules.values()):
            if hasattr(mod, key):
                getattr(mod, key).clear()


class WagtailPageTests(WagtailTestUtils, TestCase):
    """
    A set of asserts to help write tests for your own Wagtail site.
    """
    def setUp(self):
        super(WagtailPageTests, self).setUp()
        self.login()

    def _testCanCreateAt(self, parent_model, child_model):
        child_ct = ContentType.objects.get_for_model(child_model)
        parent_ct = ContentType.objects.get_for_model(parent_model)

        return all([
            child_ct in parent_model.allowed_subpage_types(),
            # Anything can be created under a Page
            parent_model is Page or parent_ct in child_model.allowed_parent_page_types()])

    def assertCanCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can be created under a parent
        Page type.
        """
        if not self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(msg, "Can not create a %s.%s under a %s.%s" % (
                child_model._meta.app_label, child_model._meta.model_name,
                parent_model._meta.app_label, parent_model._meta.model_name))
            raise self.failureException(msg)

    def assertCanNotCreateAt(self, parent_model, child_model, msg=None):
        """
        Assert a particular child Page type can not be created under a parent
        Page type.
        """
        if self._testCanCreateAt(parent_model, child_model):
            msg = self._formatMessage(msg, "Can create a %s.%s under a %s.%s" % (
                child_model._meta.app_label, child_model._meta.model_name,
                parent_model._meta.app_label, parent_model._meta.model_name))
            raise self.failureException(msg)

    def assertCanCreate(self, parent, child_model, data, msg=None):
        """
        Assert that a child of the given Page type can be created under the
        parent, using the supplied POST data
        """
        self.assertCanCreateAt(parent.specific_class, child_model)

        if 'slug' not in data and 'title' in data:
            data['slug'] = slugify(data['title'])
        data['action-publish'] = 'action-publish'

        add_url = reverse('wagtailadmin_pages:add', args=[
            child_model._meta.app_label, child_model._meta.model_name, parent.pk])
        response = self.client.post(add_url, data, follow=True)

        if response.status_code != 200:
            msg = self._formatMessage(msg, 'Creating a %s.%s returned a %d' % (
                child_model._meta.app_label, child_model._meta.model_name, response.status_code))
            raise self.failureException(msg)

        if response.redirect_chain == []:
            if 'form' not in response.context:
                msg = self._formatMessage(msg, 'Creating a page failed unusually')
                raise self.failureException(msg)
            form = response.context['form']
            if not form.errors:
                msg = self._formatMessage(msg, 'Creating a page failed for an unknown reason')
                raise self.failureException(msg)

            errors = '\n'.join('  %s:\n    %s' % (field, '\n    '.join(errors))
                               for field, errors in sorted(form.errors.items()))
            msg = self._formatMessage(msg, 'Validation errors found when creating a %s.%s:\n%s' % (
                child_model._meta.app_label, child_model._meta.model_name, errors))
            raise self.failureException(msg)

        explore_url = 'http://testserver' + reverse('wagtailadmin_explore', args=[parent.pk])
        if response.redirect_chain != [(explore_url, 302)]:
            msg = self._formatMessage(msg, 'Creating a page %s.%s didnt redirect the user to the explorer, but to %s' % (
                child_model._meta.app_label, child_model._meta.model_name,
                response.redirect_chain))
            raise self.failureException(msg)
