from django import forms
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import format_html, escape

from django.contrib.staticfiles.storage import staticfiles_storage


class TinyMceWidget(forms.Textarea):

    def __init__(self, *args, **kwargs):
        super(TinyMceWidget, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'tinymce-widget'

    class Media:
        js = (
            staticfiles_storage.url('admin.js'),
            staticfiles_storage.url('admin/js/tinymce_setup.js')
        )

        css = {
            'all': (staticfiles_storage.url('admin.css'),)
        }


class GridManagerWidget(forms.Widget):

    def __init__(self, *args, **kwargs):
        super(GridManagerWidget, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'gridmanager-widget'

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        input_attrs = self.build_attrs(attrs, name=name)
        canvas_attrs = self.build_attrs(name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            input_attrs['value'] = escape(value).encode('ascii', 'ignore')
        return format_html('<div class="gridmanager-widget-wrap"><input{} type="hidden" /><div class="gridmanager-widget-editor"/></div>', flatatt(input_attrs), flatatt(canvas_attrs))

    class Media:
        js = (
            staticfiles_storage.url('admin.js'),
            staticfiles_storage.url('admin/js/gridmanager_setup.js')
        )

        css = {
            'all': (staticfiles_storage.url('admin.css'),)
        }
