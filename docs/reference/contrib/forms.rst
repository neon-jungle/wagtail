
.. _form_builder:

Form builder
============

The ``wagtailforms`` module allows you to set up single-page forms, such as a 'Contact us' form, as pages of a Wagtail site. It provides a set of base models that site implementers can extend to create their own ``FormPage`` type with their own site-specific templates. Once a page type has been set up in this way, editors can build forms within the usual page editor, consisting of any number of fields. Form submissions are stored for later retrieval through a new 'Forms' section within the Wagtail admin interface.


Usage
~~~~~

Add ``wagtail.wagtailforms`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
       ...
       'wagtail.wagtailforms',
    ]

Within the ``models.py`` of one of your apps, create a model that extends both :class:`wagtail.wagtailforms.models.FormPageMixin` and :class:`~wagtail.wagtailcore.models.Page`:


.. code-block:: python

    from modelcluster.fields import ParentalKey
    from wagtail.wagtailadmin.edit_handlers import (
        FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel)
    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailforms.models import FormPageMixin, AbstractFormField

    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')

    class FormPage(FormPageMixin, Page):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
        ]

As illustrated above, :class:`~wagtail.wagtailforms.models.FormPageMixin` expects ``form_fields`` to be defined. Any additional fields are treated as ordinary page content - note that ``FormPage`` is responsible for serving both the form page itself and the landing page after submission, so the model definition should include all necessary content fields for both of those views.

Wagtail also provides a form mixin which emails the submission recipient defined by the editor. To achieve this form-to-email functionality, you can inherit from :class:`~wagtail.wagtailforms.models.EmailFormPageMixin` instead of :class:`~wagtail.wagtailforms.models.FormPageMixin`, and include the ``to_address``, ``from_address`` and ``subject`` fields in the ``content_panels`` definition, like so:

.. code-block:: python

    from modelcluster.fields import ParentalKey
    from wagtail.wagtailadmin.edit_handlers import (
        FieldPanel, FieldRowPanel, MultiFieldPanel)
    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailforms.models import EmailFormPageMixin, AbstractFormField

    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')

    class EmailFormPage(EmailFormPageMixin, Page):
        # ...

        content_panels = Page.content_panels + [
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
            # ...
        ]


You now need to create two templates named ``form_page.html`` and ``form_page_landing.html`` (where ``form_page`` is the underscore-formatted version of the class name). ``form_page.html`` differs from a standard Wagtail template in that it is passed a variable ``form``, containing a Django ``Form`` object, in addition to the usual ``page`` variable. A very basic template for the form would thus be:

.. code-block:: html

    {% load wagtailcore_tags %}
    <html>
        <head>
            <title>{{ page.title }}</title>
        </head>
        <body>
            <h1>{{ page.title }}</h1>
            {{ page.intro|richtext }}
            <form action="{% pageurl page %}" method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <input type="submit">
            </form>
        </body>
    </html>

``form_page_landing.html`` is a regular Wagtail template, displayed after the user makes a successful form submission.


.. _wagtailforms_formsubmissionpanel:

Displaying form submission information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``FormSubmissionsPanel`` can be added to your page's panel definitions to display the number of form submissions and the time of the most recent submission, along with a quick link to access the full submission data:

.. code-block:: python

    from wagtail.wagtailforms.edit_handlers import FormSubmissionsPanel

    class FormPage(EmailFormPageMixin, Page):
        # ...

        content_panels = Page.content_panels + [
            FormSubmissionsPanel(),
            FieldPanel('intro', classname="full"),
            # ...
        ]
