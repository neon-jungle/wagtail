from django import http
from django.apps import apps
from django.conf import settings
from django.core.urlresolvers import translate_url
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import is_safe_url
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext as _
from django.utils.translation import LANGUAGE_SESSION_KEY, check_for_language

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)

from .models import Language, TranslatedPage
from django.views.i18n import LANGUAGE_QUERY_PARAMETER, LANGUAGE_SESSION_KEY


@lru_cache()
def get_edit_handler(model):
    if hasattr(model, 'edit_handler'):
        # use the edit handler specified on the page class
        return model.edit_handler.bind_to_model(model)
    else:
        panels = extract_panel_definitions_from_model_class(model, exclude={'language', 'parent'})
        return ObjectList(panels).bind_to_model(model)


def translate(request, app_label, model_name, pk, language):
    language = get_object_or_404(Language, code=language)
    try:
        PageModel = apps.get_model(app_label, model_name)
    except LookupError:
        raise Http404
    if not issubclass(PageModel, TranslatedPage):
        raise Http404
    page = get_object_or_404(PageModel, pk=pk)

    try:
        instance = page.translations.get(language=language)
    except PageModel.Translation.DoesNotExist:
        instance = PageModel.Translation(parent=page, language=language)
    page.translation = instance

    EditHandler = get_edit_handler(PageModel.Translation)
    EditForm = EditHandler.get_form_class(PageModel.Translation)

    if request.POST:
        form = EditForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, _('{translation} was saved').format(
                translation=form.instance))
            # we're done here - redirect back to the explorer
            return redirect('wagtailadmin_explore', page.get_parent().id)
        else:
            messages.error(request, _('Fix the errors below'))
    else:
        form = EditForm(instance=instance)

    edit_handler = EditHandler(instance=instance, form=form)

    return render(request, 'wagtailtranslations/translate.html', {
        'language': language,
        'edit_handler': edit_handler,
        'instance': instance,
        'form': form,
        'page': page,
        'model_opts': PageModel._meta,
    })


def set_language(request):
    """
    Redirect to a given url while setting the chosen language in the
    session or cookie. The url and the language code need to be
    specified in the request parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    """
    next = request.POST.get('next', request.GET.get('next'))
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')
        if not is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = http.HttpResponseRedirect(next)
    if request.method == 'POST':
        lang_code = request.POST.get(LANGUAGE_QUERY_PARAMETER)
        try:
            language = Language.objects.active().get(code=lang_code)
        except Language.DoesNotExist:
            pass
        else:
            next_trans = translate_url(next, lang_code)
            if next_trans != next:
                response = http.HttpResponseRedirect(next_trans)
            set_language_for_request(request, response, language)
    return response


def set_language_for_request(request, response, language):
    if hasattr(request, 'session'):
        request.session[LANGUAGE_SESSION_KEY] = language.code
    else:
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language.code,
                            max_age=settings.LANGUAGE_COOKIE_AGE,
                            path=settings.LANGUAGE_COOKIE_PATH,
                            domain=settings.LANGUAGE_COOKIE_DOMAIN)
