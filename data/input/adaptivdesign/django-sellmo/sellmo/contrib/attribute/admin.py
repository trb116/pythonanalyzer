# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from functools import partial

from django.contrib import admin
from django.contrib.admin import widgets
from django.utils.translation import ugettext_lazy as _

from .models import AttributeSet, Value
from .forms import ProductAttributeFormFactory


class BaseProductAttributeMixin(object):
    def get_attribute_formfactory(
        self,
        request,
        factory,
        obj=None,
        prefix=None,
        mixin=None,
        **kwargs
    ):

        # Since attribute_set can have changed by a submit, we fetch the attrbute set
        # from the persisted (old) obj.
        attribute_set = None
        if obj:
            if not hasattr(obj, '_attribute_set'):
                attribute_set = self.model.objects.get(pk=obj.pk).attribute_set
                obj._attribute_set = attribute_set
            else:
                attribute_set = obj._attribute_set
        return factory(
            form=kwargs.get('form', None),
            prefix=prefix,
            mixin=mixin,
            formfield_callback=partial(
                self.admin_attribute_formfield,
                request=request
            ),
            attribute_set=attribute_set
        )

    def admin_attribute_formfield(self, attribute, formfield, request):
        typ = attribute.get_type()
        model = typ.get_model()
        if model:
            remote_field = Value._meta.get_field(
                typ.get_value_field_name()
            ).rel
            related_modeladmin = self.admin_site._registry.get(model)
            wrapper_kwargs = {}
            if related_modeladmin:
                wrapper_kwargs.update(
                    can_add_related=related_modeladmin.has_add_permission(
                        request
                    ),
                    can_change_related=
                    related_modeladmin.has_change_permission(request),
                    can_delete_related=
                    related_modeladmin.has_delete_permission(request)
                )
            formfield.widget = widgets.RelatedFieldWidgetWrapper(
                formfield.widget, remote_field, self.admin_site,
                **wrapper_kwargs
            )
        return formfield


class ProductAttributeMixin(BaseProductAttributeMixin):
    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = (
            self.get_attribute_formfactory(
                request,
                ProductAttributeFormFactory,
                prefix='attribute',
                obj=obj,
                **kwargs
            ).factory()
        )
        return (
            super(ProductAttributeMixin, self).get_form(
                request,
                obj=obj,
                **kwargs
            )
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ProductAttributeMixin, self).get_fieldsets(
            request, obj
        )
        fields = (
            self.get_attribute_formfactory(
                request,
                ProductAttributeFormFactory,
                prefix='attribute',
                obj=obj
            ).get_attribute_formfield_names()
        )
        fieldsets += ((_("Attributes"), {'fields': fields}), )
        return fieldsets


class BaseAttributeSetAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # optimize the list display.
        return super(BaseAttributeSetAdmin,
                     self).get_queryset(request).flat_ordered()


class AttributeSetParentListFilter(admin.SimpleListFilter):

    title = _("parent attribute set")
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        return [
            (str(sett.pk), unicode(sett))
            for sett in AttributeSet.objects.all().flat_ordered()
        ]

    def queryset(self, request, queryset):
        pk = self.value()
        if pk != None:
            sett = AttributeSet.objects.get(pk=pk)
            return queryset.in_parent(sett)
        else:
            return queryset.all()
