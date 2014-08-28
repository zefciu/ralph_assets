# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# from threading import local

# from django.core import serializers

# from ralph_assets.history.models import History
# from ralph_assets.history.utils import DictDiffer


# _local_thread = local()
# serializer = serializers.get_serializer("python")()


def pre_save(sender, instance, **kwargs):
    print('PRE')  # DETELE THIS
    print(instance)  # DETELE THIS

    # if kwargs['created']:
    #     return
    # setattr(
    #     _local_thread,
    #     'post_data',
    #     serializer.serialize([instance])[0]['fields']
    # )


def post_save(sender, instance, **kwargs):
    # from ralph_assets.history import registry
    print('POST')  # DETELE THIS
    print(instance)  # DETELE THIS
    # if not getattr(_local_thread, 'post_data', None) or not instance.id:
    #     return

    # post_data = _local_thread.post_data
    # pre_data = serializer.serialize([instance])[0]['fields']
    # r = DictDiffer(post_data, pre_data)

    # diff_data = [
    #     {
    #         'field': field,
    #         'old': post_data[field],
    #         'new': pre_data[field]
    #     }
    #     for field in r.changed()
    # ]
    # History.objects.log_changes(
    #     obj=instance,
    #     diff_data=diff_data,
    # )
