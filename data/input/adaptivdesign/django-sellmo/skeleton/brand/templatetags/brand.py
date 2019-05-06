from django import template
from sellmo import modules
from sellmo.core import indexing

from classytags.core import Tag, Options
from classytags.arguments import Argument


register = template.Library()


class CategoryBrandsTag(Tag):
    name = 'categorybrands'
    options = Options(
        Argument('category'),
        'as',
        Argument('varname', default='brands', required=False, resolve=False),
        blocks=[
            ('endcategorybrands', 'nodelist')
        ],
    )

    def get_brands(self, category):
        index = indexing.indexer.get_index('product')
        if index.has_field('categories') and index.has_field('attr_brand'):
            brands = index.search().filter(categories__in=category.get_descendants(include_self=True))
            brands = brands.with_fields('attr_brand')
            return [obj['attr_brand'] for obj in brands.values()]
        else:
            return []

    def render_tag(self, context, category, varname, nodelist):
        context.push()
        context[varname] = self.get_brands(category)
        output = nodelist.render(context)
        context.pop()
        return output


register.tag(CategoryBrandsTag)
