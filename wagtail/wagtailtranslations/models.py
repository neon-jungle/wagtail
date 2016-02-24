from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase
from django.utils import six
from django.utils.translation import get_language
from django.utils.functional import cached_property

from wagtail.wagtailcore.models import (
    PageManager, Page, PageBase)


def get_current_or_default_language():
    return get_language() or settings.LANGUAGE_CODE


class TranslationQuerySet(models.QuerySet):
    def current_then_default(self):
        default_language = settings.LANGUAGE_CODE
        current_language = get_current_or_default_language()

        if default_language == current_language:
            return self.filter(language=current_language)

        # Use the default language as a fallback if the current language does
        # not exist
        languages = [current_language, default_language]
        qs = self.filter(language__in=languages).order_by('language')
        # Ensure the current language precedes the default language
        if current_language > default_language:
            qs = qs.reverse()
        return qs


class Translation(models.Model):
    language = models.CharField(choices=settings.LANGUAGES, max_length=10)

    objects = TranslationQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = [['page', 'language']]

    def __str__(self):
        return '{} translation for {}'.format(self.language, self.page)


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


class TranslatedPageBase(PageBase):
    def __new__(mcs, name, bases, attrs):
        if 'TranslatedFields' not in attrs:
            return super(TranslatedPageBase, mcs).__new__(mcs, name, bases, attrs)

        TranslatedFields = attrs.pop('TranslatedFields')

        cls = super(TranslatedPageBase, mcs).__new__(mcs, name, bases, attrs)

        if not cls._meta.abstract and type(cls.objects) in (models.Manager, PageManager):
            TranslatedPageManager().contribute_to_class(cls, 'objects')

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
            'page': models.ForeignKey(cls, on_delete=models.CASCADE,
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


class TranslatedPageManager(PageManager):
    def get_queryset(self):
        # Automatically prefetch the translation for the current language
        return super(TranslatedPageManager, self).get_queryset().prefetch_related(
            LanguagePrefetch(self.model.Translation))


class TranslatedPage(six.with_metaclass(TranslatedPageBase, Page)):

    _translation = None
    _prefetched_translations = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(TranslatedPage, self).__init__(*args, **kwargs)

    @cached_property
    def translation(self):
        current_language = get_current_or_default_language()

        # Try and use the prefetched translation, if used
        if self._prefetched_translations is not None:
            try:
                translation = self._prefetched_translations[0]
            except IndexError:
                pass

        # Otherwise, try and pull an existing translation from the database
        elif self.pk is not None:
            translation = self.translations.current_then_default().first()

        # Other otherwise, make an empty translation
        if translation is None:
            translation = self.Translation(page=self, language=current_language)

        return translation
