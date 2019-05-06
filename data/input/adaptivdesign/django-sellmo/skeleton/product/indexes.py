from sellmo import modules
from sellmo.core import indexing
from sellmo.core.loading import load



def upload_image_to(instance, filename):
    return os.path.join('product', instance.slug, filename)



@load(before='finalize_product_ProductIndex')
def load_model():
    class ProductIndex(modules.product.ProductIndex):

        name = indexing.CharField(
            max_length=255,
            populate_value_cb=(lambda document, **variety: document.name))

    modules.product.ProductIndex = ProductIndex
