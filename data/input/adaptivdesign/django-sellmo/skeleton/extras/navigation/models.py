from extras.navigation.fields import ViewField
from extras.navigation.registration import registry
from extras.navigation.constants import PLACEMENT_CHOICES

from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey, TreeManager


class NavigationItemQuerySet(QuerySet):

    def in_parent(self, parent, recurse=True):
        if parent is not None:
            q = self.filter(tree_id=parent.tree_id)
            if recurse:
                return q.filter(level__gt=parent.level)
            else:
                return q.filter(level=parent.level + 1)
        else:
            return self.filter(parent=None)

    def flat_ordered(self):
        return self.order_by('tree_id', 'lft')


class NavigationItemManager(TreeManager):
    pass


class NavigationItem(MPTTModel):

    objects = NavigationItemManager.from_queryset(NavigationItemQuerySet)()

    title = models.CharField(
        max_length=80,
        verbose_name=_("title"),
    )

    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        verbose_name=_("parent navigation item"),
        related_name='children'
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=(
            "Inactive navigation items will be hidden from the site."
        )
    )

    placement = models.CharField(
        max_length=80,
        choices=PLACEMENT_CHOICES,
        verbose_name=_("placement"),
        default=PLACEMENT_CHOICES[0][0],
    )

    sort_order = models.SmallIntegerField(
        default=0,
        verbose_name=_("sort order"),
    )

    view = ViewField(
        verbose_name=_("view"),
        blank=True,
    )

    def get_absolute_url(self):
        url = self.reversed_url
        if url:
           return url
        return '/'

    @property
    def registration(self):
        try:
            return registry[self.view]
        except KeyError:
            return None

    @property
    def kwargs(self):
        kwargs = {}
        for argument in self.arguments.all():
            kwargs[argument.argument_name] = argument.argument
        return kwargs

    @property
    def mapped_kwargs(self):
        view = self.registration
        if view:
            return view.map_kwargs(self.kwargs)
        else:
            return None

    def get_reversed_url(self, namespace=None):
        view = self.view
        if namespace:
            view = '{0}:{1}'.format(namespace, view)
        try:
            return reverse(view, kwargs=self.mapped_kwargs)
        except NoReverseMatch as ex:
            return None

    reversed_url = property(get_reversed_url)

    def get_full_title(self, ancestors=None):
        if ancestors is None:
            ancestors = self.get_ancestors(include_self=True)
        else:
            ancestors = ancestors + [self]
        return " | ".join(item.title for item in ancestors)

    full_title = property(get_full_title)

    def clean(self):
        if self.parent == self:
            raise ValidationError(_("Cannot assign self as parent navigation item."))

    def save(self):
        if self.parent:
            self.placement = self.parent.placement
        super(NavigationItem, self).save()
        for child in self.children.exclude(placement=self.placement):
            child.placement = self.placement
            child.save()

    def __unicode__(self):
        return self.title

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'title']

    class Meta:
        app_label = 'navigation'
        verbose_name = _("navigation item")
        verbose_name_plural = _("navigation items")

class NavigationArgument(models.Model):

    item = models.ForeignKey(
        'navigation.NavigationItem',
        editable = False,
        related_name = 'arguments',
    )

    argument_name = models.CharField(
        max_length=255,
    )

    argument_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True
    )

    argument_object_id = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    argument_object = generic.GenericForeignKey(
        'argument_content_type',
        'argument_object_id'
    )

    argument_value = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    @property
    def argument(self):
        if self.argument_object:
            return self.argument_object
        return self.argument_value

    def __unicode__(self):
        return u"%s: %s" % (self.argument_name, self.argument)

    class Meta:
        app_label = 'navigation'
        verbose_name = _("navigation argument")
        verbose_name_plural = _("navigation arguments")

# Cache invalidation
def on_cache_invalidation(sender, instance, **kwargs):
    cache_keys = cache.get('navigation_cache_keys', [])
    cache.delete_many(cache_keys + ['navigation_cache_keys'])


post_save.connect(on_cache_invalidation, sender=NavigationItem)
post_save.connect(on_cache_invalidation, sender=NavigationArgument)
post_delete.connect(on_cache_invalidation, sender=NavigationItem)
post_delete.connect(on_cache_invalidation, sender=NavigationArgument)
