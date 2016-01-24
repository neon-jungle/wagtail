from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.db.models import Q
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import send_notification
from wagtail.wagtailcore.models import PageRevision

from . import BaseModerationWorkflow


class StandardWorkflow(BaseModerationWorkflow):
    def can_submit_for_moderation(self, page, user):
        """ All users can submit pages for moderation """
        return True

    def can_publish(self, page, user):
        """
        Users can publish if they have been granted the publish permission
        """
        perms_helper = page.permissions_for_user(user)
        return perms_helper.can_publish()

    def revisions_for_moderation(self, user):
        """ Users can moderate any page they have permission to publish """
        # Deal with the trivial cases first...
        if not self.user.is_active:
            return PageRevision.objects.none()
        if self.user.is_superuser:
            return PageRevision.submitted_revisions.all()

        # get the list of pages for which they have direct publish permission
        # (i.e. they can publish any page within this subtree)
        publishable_pages = [perm.page for perm in self.permissions if perm.permission_type == 'publish']
        if not publishable_pages:
            return PageRevision.objects.none()

        # compile a filter expression to apply to the PageRevision.submitted_revisions manager:
        # return only those pages whose paths start with one of the publishable_pages paths
        only_my_sections = Q()
        for page in publishable_pages:
            only_my_sections = only_my_sections | Q(page__path__startswith=page.path)

        # return the filtered queryset
        return PageRevision.submitted_revisions.filter(only_my_sections)

    def submit_for_moderation(self, page_revision, user):
        """ Nothing special needs to happen here """
        send_notification(page_revision.id, 'submitted', user.id)

    def approve(self, request, page_revision, user):
        if not page_revision.page.permissions_for_user(user).can_publish():
            raise PermissionDenied

        if not page_revision.submitted_for_moderation:
            messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(page_revision.page.title))
            return redirect('wagtailadmin_home')

        if request.method == 'POST':
            page_revision.approve_moderation()
            messages.success(request, _("Page '{0}' published.").format(page_revision.page.title), buttons=[
                messages.button(page_revision.page.url, _('View live')),
                messages.button(reverse('wagtailadmin_pages:edit', args=(page_revision.page.id,)), _('Edit'))
            ])
            send_notification(page_revision.id, 'approved', user.id)

        return redirect('wagtailadmin_home')

    def reject(self, request, page_revision, user):
        if not page_revision.page.permissions_for_user(user).can_publish():
            raise PermissionDenied

        if not page_revision.submitted_for_moderation:
            messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(page_revision.page.title))
            return redirect('wagtailadmin_home')

        if request.method == 'POST':
            page_revision.reject_moderation()
            messages.success(request, _("Page '{0}' rejected for publication.").format(page_revision.page.title), buttons=[
                messages.button(reverse('wagtailadmin_pages:edit', args=(page_revision.page.id,)), _('Edit'))
            ])
            send_notification(page_revision.id, 'rejected', user.id)

        return redirect('wagtailadmin_home')
