# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User, Group
from django.db import models
from datetime import date
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.utils.encoding import python_2_unicode_compatible
from .fields import HexIntegerField
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS
from fcm.models import AbstractDevice
from  django.core.validators import validate_comma_separated_integer_list


class MobileUser(models.Model):
    id = models.BigIntegerField(primary_key = True)
    name = models.CharField(max_length=110, default = 'empty')
    description = models.CharField(max_length=200, default = 'empty')
    image = models.ImageField(upload_to='media/profiles/',null=True, default = 'media/profiles/None/no-img.jpg', max_length=255)
    image_url = models.CharField(max_length=200, default='null')
    def __str__(self):              # __unicode__ on Python 2
      return self.name


class Events(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.IntegerField(default=1)
    latitude = models.CharField(max_length=20, default = '45.10')
    longitude = models.CharField(max_length=20, default = '-73.30')
    number_invited = models.IntegerField(default = 0)
    event_admin = models.IntegerField(default =1)
    event_admin_name = models.CharField(max_length=200,default ='Anonymous')
    is_private = models.BooleanField(default = False)
    title = models.CharField(max_length=150, default = 'Title ')
    description = models.CharField(max_length=150, default = 'Description ')
    address = models.CharField(max_length=150, default = ' ')
    image = models.ImageField(upload_to='media/events/', default='media/events/None/no-img.jpg', null=True, max_length=255)
    image_url = models.CharField(max_length=200, default="null" )
    city = models.IntegerField(default=1000)
    cluster_id = models.IntegerField(default=1000)


    def __str__(self):              # __unicode__ on Python 2
     return self.title
