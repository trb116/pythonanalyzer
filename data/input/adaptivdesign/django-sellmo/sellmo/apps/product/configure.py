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

from django.db.models.signals import post_save, pre_delete

from sellmo.core import indexing
from sellmo.apps.customer.models import CustomerGroup # NOQA

from .models import Product # NOQA
from .indexes import ProductIndex # NOQA

indexing.indexer.register_index('product', ProductIndex)


def on_product_post_save(sender, instance, raw=False, **kwargs):
    if not raw:
        index = indexing.indexer.get_index('product')
        index.sync([instance.pk])


def on_product_pre_delete(sender, instance, **kwargs):
    index = indexing.indexer.get_index('product')
    index.sync([instance.pk])


def on_customer_group_post_save(sender, instance, raw=False, **kwargs):
    if not raw:
        index = indexing.indexer.get_index('product')
        index.sync()


def on_customer_group_pre_delete(sender, instance, **kwargs):
    index = indexing.indexer.get_index('product')
    index.sync()


def connect_signals():
    for subtype in Product.SUBTYPES + [Product]:
        post_save.connect(on_product_post_save, sender=subtype)
        pre_delete.connect(on_product_pre_delete, sender=subtype)

    post_save.connect(on_customer_group_post_save, sender=CustomerGroup)
    pre_delete.connect(on_customer_group_pre_delete, sender=CustomerGroup)
