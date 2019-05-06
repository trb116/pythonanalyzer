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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo.core.loading import load
from sellmo.core import indexing

import sellmo.apps.product as _product


@load(before='finalize_product_Product')
def load_model():
    class Product(_product.models.Product):

        active = models.BooleanField(
            default=True,
            verbose_name=_("active"),
            help_text=_(
                "Inactive products will be hidden from the site."
            )
        )

        featured = models.BooleanField(
            default=False,
            verbose_name=_("featured"),
            help_text=_(
                "Marks this product as featured allowing "
                "additional showcasing across the site."
            )
        )

        class Meta(_product.models.Product.Meta):
            abstract = True

    _product.models.Product = Product


@load(before='finalize_product_ProductIndex')
def load_index():
    class ProductIndex(_product.indexes.ProductIndex):
        active = indexing.BooleanField(
            populate_value_cb=(lambda document, **variety: document.active)
        )

        featured = indexing.BooleanField(
            populate_value_cb=(lambda document, **variety: document.featured)
        )

    _product.indexes.ProductIndex = ProductIndex
