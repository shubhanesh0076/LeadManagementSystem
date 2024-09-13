from utilities import utils
from permissions.models import Role
from django.db.models.signals import pre_save


def pre_save_receiver(sender, instance, *args, **kwargs): 
    if not instance.slug: 
       instance.slug = utils.unique_slug_generator(instance, instance.role_name) 
pre_save.connect(pre_save_receiver, sender = Role)