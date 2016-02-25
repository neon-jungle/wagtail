from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from wagtail.wagtailcore.models import Page, PageBase, PageManager
from wagtail.wagtailsnippets.models import register_snippet


def get_current_or_default_language():
    return get_language() or settings.LANGUAGE_CODE


class LanguageQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)


@register_snippet
@python_2_unicode_compatible
class Language(models.Model):
    code = models.CharField(
        max_length=10, choices=settings.LANGUAGES, unique=True)
    name_override = models.CharField(
        blank=True, max_length=100,
        help_text=_('Override the default name displayed for this language. Leave this field blank to use the default name.'))
    active = models.BooleanField(
        default=True,
        help_text=_('Whether this language is available to visitors'))

    objects = LanguageQuerySet.as_manager()

    class Meta:
        ordering = ['code']

    @property
    def name(self):
        return self.name_override or self.get_code_display()

    def __str__(self):
        return self.name


class TranslationQuerySet(models.QuerySet):
    def current_then_default(self):
        default_language = settings.LANGUAGE_CODE
        current_language = get_current_or_default_language()

        if default_language == current_language:
            return self.filter(language__code=current_language)

        # Use the default language as a fallback if the current language does
        # not exist
        languages = [current_language, default_language]
        qs = self.filter(language__code__in=languages).order_by('language__code')
        # Ensure the current language precedes the default language
        if current_language > default_language:
            qs = qs.reverse()
        return qs


class Translation(models.Model):
    language = models.ForeignKey(Language)

    objects = TranslationQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = [['parent', 'language']]

    def __str__(self):
        return '{} translation for {}'.format(self.language, self.parent)


class TranslatedField(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance.translation, self.field_name)

    def __set__(self, instance, value):
        setattr(instance.translation, self.field_name, value)

    def __delete__(self, instance):
        delattr(instance.translation, self.field_name)


class TranslatedModelBase(ModelBase):
    def __new__(mcs, name, bases, attrs):
        if 'TranslatedFields' not in attrs:
            return super(TranslatedModelBase, mcs).__new__(mcs, name, bases, attrs)

        TranslatedFields = attrs.pop('TranslatedFields')

        cls = super(TranslatedModelBase, mcs).__new__(mcs, name, bases, attrs)

        fields = {
            attr: value for attr, value in TranslatedFields.__dict__.items()
            if isinstance(value, models.Field)}
        Translation = mcs.make_translation_model(cls, fields)
        setattr(cls, 'Translation', Translation)

        for field_name in fields.keys():
            setattr(cls, field_name, TranslatedField(field_name))

        return cls

    @classmethod
    def make_translation_model(mcs, cls, fields):
        name = cls.__name__ + 'Translation'
        attrs = {
            '__module__': cls.__module__,
            'parent': models.ForeignKey(cls, on_delete=models.CASCADE,
                                      related_name='translations')}
        attrs.update(fields)

        return ModelBase(name, (Translation,), attrs)


class LanguagePrefetch(models.Prefetch):
    """
    Prefetch the current language translation
    """
    def __init__(self, translation_model):
        super(LanguagePrefetch, self).__init__('translations', to_attr='_prefetched_translations')
        self.translation_model = translation_model

    def _get_queryset(self):
        qs = self.translation_model.objects.current_then_default()
        return qs

    def _set_queryset(self, value):
        assert value is None

    queryset = property(_get_queryset, _set_queryset)


class TranslatedModelManager(models.Manager):
    def get_queryset(self):
        # Automatically prefetch the translation for the current language
        return super(TranslatedModelManager, self).get_queryset().prefetch_related(
            LanguagePrefetch(self.model.Translation))


class TranslatedModel(six.with_metaclass(TranslatedModelBase, models.Model)):

    _translation = None
    _prefetched_translations = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(TranslatedModel, self).__init__(*args, **kwargs)

    @cached_property
    def translation(self):
        current_language = get_current_or_default_language()

        # Try and use the prefetched translation, if used
        if self._prefetched_translations is not None:
            try:
                return self._prefetched_translations[0]
            except IndexError:
                pass

        # Otherwise, try and pull an existing translation from the database
        elif self.pk is not None:
            return self.translations.current_then_default().first()

        # Other otherwise, make an empty translation
        return self.Translation(parent=self, language=current_language)


class TranslatedPageManager(TranslatedModelManager, PageManager):
    pass


class TranslatedPageBase(TranslatedModelBase, PageBase):
    def __new__(mcs, name, bases, attrs):
        cls = super(TranslatedPageBase, mcs).__new__(mcs, name, bases, attrs)
        if not cls._meta.abstract and type(cls.objects) in (models.Manager, PageManager):
            TranslatedPageManager().contribute_to_class(cls, 'objects')
        return cls


class TranslatedPage(six.with_metaclass(TranslatedPageBase, TranslatedModel, Page)):
    objects = TranslatedPageManager()

    class Meta:
        abstract = True
