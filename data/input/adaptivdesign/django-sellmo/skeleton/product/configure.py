from sellmo import modules
from sellmo.core.loading import load


@load(after='register_product_subtypes')
@load(action='register_variation_product_subtypes')
def register_variation_product_subtypes():
    modules.variation.register_product_subtype(modules.product.SimpleProduct)
