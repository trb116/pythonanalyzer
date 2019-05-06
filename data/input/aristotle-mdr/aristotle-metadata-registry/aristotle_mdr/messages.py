from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from notifications.signals import notify

from aristotle_mdr.utils import url_slugify_concept, url_slugify_workgroup


def favourite_updated(recipient, obj):
    notify.send(obj, recipient=recipient, verb="A favourited item has been changed:", target=obj)


def workgroup_item_updated(recipient, obj):
    notify.send(obj, recipient=recipient, verb="was modified in the workgroup", target=obj.workgroup)


def workgroup_item_new(recipient, obj):
    notify.send(obj, recipient=recipient, verb="was modified in the workgroup", target=obj.workgroup)


def new_comment_created(comment):
    post = comment.post
    author_name = comment.author.get_full_name() or comment.author
    notify.send(comment.author, recipient=post.author, verb="commented on your post", target=post)


def new_post_created(post, recipient):
    op_name = post.author.get_full_name() or post.author
    notify.send(post.author, recipient=recipient, verb="made a new post", target=post, action_object=post.workgroup)
