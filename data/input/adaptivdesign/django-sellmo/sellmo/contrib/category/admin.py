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

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Category


class BaseCategoryAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # optimize the list display.
        return super(
            BaseCategoryAdmin, self
        ).get_queryset(request).flat_ordered()


class ProductCategoriesMixin(object):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'categories':
            kwargs['queryset'] = Category.objects.all() \
                                        .prefetch_related('parent') \
                                        .flat_ordered()
        return super(ProductCategoriesMixin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )


class ProductCategoryListFilter(admin.SimpleListFilter):
    title = _("category")
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return [
            (str(category.pk), unicode(category))
            for category in Category.objects.all().flat_ordered()
        ]

    def queryset(self, request, queryset):
        pk = self.value()
        if pk != None:
            category = Category.objects.get(pk=pk)
            return queryset.in_category(category)
        else:
            return queryset.all()


class CategoryParentListFilter(admin.SimpleListFilter):
    title = _("parent category")
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        return [
            (str(category.pk), unicode(category))
            for category in Category.objects.all().flat_ordered()
        ]

    def queryset(self, request, queryset):
        pk = self.value()
        if pk != None:
            category = Category.objects.get(pk=pk)
            return queryset.in_parent(category)
        else:
            return queryset.all()
