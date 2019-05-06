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

from django.db.models.signals import pre_save, post_save, pre_delete

from sellmo import celery
from sellmo.core import indexing
from sellmo.contrib.attribute.models import Value

from .signals import variations_invalidated, variations_synced
from .models import Variation


def on_variations_synced(sender, product, **kwargs):
    index = indexing.indexer.get_index('product')
    index.sync([product.pk])


variations_synced.connect(on_variations_synced)

if celery.enabled:
    from . import tasks

    def on_variations_invalidated(sender, product, **kwargs):
        tasks.sync_variations.delay(product)

    variations_invalidated.connect(on_variations_invalidated)


def on_value_pre_save(sender, instance, raw=False, *args, **kwargs):
    if raw:
        return

    product = instance.product.downcast()
    instance.base_product = None
    if product.is_variant:
        instance.base_product = product.product


def on_value_post_save(sender, instance, raw=False, *args, **kwargs):
    if raw:
        return

    product = instance.base_product if instance.base_product else instance.product
    Variation.objects.invalidate(product)


def on_value_pre_delete(sender, instance, *args, **kwargs):
    product = instance.base_product if instance.base_product else instance.product
    Variation.objects.invalidate(product)


pre_save.connect(on_value_pre_save, sender=Value)
post_save.connect(on_value_post_save, sender=Value)
pre_delete.connect(on_value_pre_delete, sender=Value)
