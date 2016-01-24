from django.conf import settings
from django.utils.lru_cache import lru_cache
from django.utils.module_loading import import_string


class BaseModerationWorkflow(object):
    def can_submit_for_moderation(self, page, user):
        """
        Can the user submit a revision of the page for moderation.

        This check does not need to check if the user is allowed to actually
        create a page, or other permission checks. It can assume the user is
        otherwise allowed to create a page in this location.
        """
        raise NotImplementedError()

    def can_publish(self, page, user):
        """
        Can the user publish changes to the page, without submitting the
        changes for moderation.

        This check does not need to check if the user is allowed to actually
        create a page, or other permission checks. It can assume the user is
        otherwise allowed to create a page in this location.
        """
        raise NotImplementedError()

    def can_moderate(self, page, user):
        """
        Can a user moderate a page, assuming the page is available for
        moderation.
        """
        return self.revisions_for_moderation(user).filter(pk=page.pk).exists()

    def revisions_for_moderation(self, user):
        """
        Get a QuerySet of all pages the user can moderate. This only includes
        pages that currently have pending changes, not all pages the user could
        moderate.
        """
        raise NotImplementedError()

    def submit_for_moderation(self, request, page_revision, user):
        """
        Submit a page revision by a user for moderation.
        """
        raise NotImplementedError()

    def approve(self, request, page_revision, user):
        """
        The moderator has approved the page revision for publication.

        This can optionally return an HttpResponse, which will be used as the
        response in place of the default, which redirects the user to the page
        explorer
        """
        raise NotImplementedError()

    def reject(self, request, page_revision, user):
        """
        The moderator has approved the page revision for publication.

        This can optionally return an HttpResponse, which will be used as the
        response in place of the default, which redirects the user to the page
        explorer
        """
        raise NotImplementedError()



@lru_cache()
def get_moderation_workflow():
    if hasattr(settings, 'WAGTAIL_MODERATION_WORKFLOW'):
        path = getattr(settings, 'WAGTAIL_MODERATION_WORKFLOW')
        cls = import_string(path)
    else:
        cls = StandardWorkflow
    return cls()
