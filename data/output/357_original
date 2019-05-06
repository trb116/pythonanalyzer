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

from django.db.models.signals import m2m_changed, post_save, post_delete

from sellmo import params, caching
from sellmo.core import indexing
from sellmo.apps.product.models import Product

from .models import Category

template_cache = None
if caching.enabled:
    from sellmo.contrib.category.caches import template_cache


def on_cache_invalidation(sender, instance, raw=False, **kwargs):

    if raw:
        return

    if template_cache is not None and template_cache.supports_tags():
        template_cache.delete(tags=['categories'])


post_save.connect(on_cache_invalidation, sender=Category)
post_delete.connect(on_cache_invalidation, sender=Category)


def on_categories_m2m_changed(sender, instance, action, reverse, **kwargs):

    if params.loaddata:
        return

    if action in ('post_add', 'post_remove', 'post_clear'):
        index = indexing.indexer.get_index('product')
        if not reverse:
            index.sync([instance.pk])
        else:
            products = Product.objects.for_relatable(instance)
            index.sync(products)


m2m_changed.connect(on_categories_m2m_changed,
                    sender=Product.categories.through)


def on_categories_m2m_changed(sender, instance, action, reverse, pk_set,
                              **kwargs):

    if params.loaddata:
        return

    if action in ('post_add', 'post_remove', 'post_clear'):
        if not reverse:
            instance.update_primary_category()
        else:
            for pk in pk_set:
                product = Product.objects.get(pk=pk)
                product.update_primary_category()


m2m_changed.connect(on_categories_m2m_changed,
                    sender=Product.categories.through)
