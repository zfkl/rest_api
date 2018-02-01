# -*- coding: utf-8 -*-
"""
REST API View for GET and POST
Models for MobileUser and Event
MobileUser reprensents data for android users
Event represents an event data for an event
"""
from __future__ import unicode_literals
from django.db import models

class MobileUser(models.Model):
    """data reprensation for android users in database
    """
    name = models.CharField(max_length=110, default='empty')
    description = models.CharField(max_length=200, default='empty')
    image = models.ImageField(upload_to='media/profiles/', null=True, \
    default='media/profiles/None/no-img.jpg', max_length=255)
    image_url = models.CharField(max_length=200, default='null')

    def __str__(self):              # __unicode__ on Python 2
        """get user name, ex when MobileUser.objects.get(id=1) = john doe"""
        return self.name


class Events(models.Model):
    """data representation for event in database
    """
    category = models.IntegerField(default=1)
    #todo change default gps from android
    latitude = models.CharField(max_length=20, default='45.10')
    longitude = models.CharField(max_length=20, default='-73.30')
    number_invited = models.IntegerField(default=0)
    event_admin = models.IntegerField(default=1)
    event_admin_name = models.CharField(max_length=250, default='Anonymous')
    is_private = models.BooleanField(default=False)
    title = models.CharField(max_length=150, default='Title ')
    description = models.CharField(max_length=150, default='Description ')
    address = models.CharField(max_length=150, default=' ')
    image = models.ImageField(upload_to='media/events/', default='media/events/None/no-img.jpg', \
    null=True, max_length=255)
    image_url = models.CharField(max_length=200, default="null")
    city = models.IntegerField(default=1000)
    cluster_id = models.IntegerField(default=1000)


    def __str__(self):              # __unicode__ on Python 2
        """get event title, ex: Event.objects.get(id=1) = fete quartier latin"""
        return self.title
