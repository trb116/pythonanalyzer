from django.db import models
from django.template.response import TemplateResponse

from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailadmin.edit_handlers import (FieldPanel, MultiFieldPanel,
    InlinePanel, PageChooserPanel, StreamFieldPanel)


from modelcluster.fields import ParentalKey
from store.blocks import FeaturetteItemBlock, InverseFeaturetteItemBlock, CarouselBlock, FeaturedProductsBlock

class StoreIndexPage(Page):
    """
    Example integration of Sellmo with wagtail.
    """

    template = 'store/index.html'
    subpage_types = ['store.StorePage']
    parent_page_types = []

    body = StreamField([
        ('paragraph', blocks.RichTextBlock(icon='pilcrow')),
        ('featurette', FeaturetteItemBlock()),
        ('inverse_featurette', InverseFeaturetteItemBlock()),
        ('carousel', CarouselBlock()),
        ('featured_products', FeaturedProductsBlock()),
    ])

    content_panels = [
        FieldPanel('title'),
        StreamFieldPanel('body'),
    ]


class StorePage(Page):
    template = 'store/page.html'

    body = StreamField([
        ('paragraph', blocks.RichTextBlock(icon='pilcrow')),
        ('featurette', FeaturetteItemBlock()),
        ('inverse_featurette', InverseFeaturetteItemBlock()),
        ('carousel', CarouselBlock())
    ])

    content_panels = [
        FieldPanel('title'),
        StreamFieldPanel('body'),
    ]
