# -*- coding: utf-8 -*-
"""
REST API View for GET and POST
GET allows authenticated user to have JSON from Event model
?{id} single event
?{cluster_id, city} all events in a cluster of a city , ex: in Parc Lafontaine

POST allows users to create their own events or duplicate an event they like
?{id} the event with this id will be duplicate and the owner is the user from request

"""
import os
import re
import boto3
import numpy as np
from prototype.serializers import EventsSerializer
from prototype.settings import settings as SETTINGS


#clusters contains GPS data
from prototype.clusters import WORLD_GPS, GPS_CITIES

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser

from geopy.distance import vincenty
from .models import Event, MobileUser

#import config variables from settings for more security
PRODUCTION_SERVERS = 'PRODUCTION'
if os.environ['COMPUTER'] == PRODUCTION_SERVERS:
    ACCESS_KEY = SETTINGS.AWS_S3_ACCESS_KEY_ID
    SECRET_KEY = SETTINGS.AWS_S3_SECRET_ACCESS_KEY
    BUCKET_NAME = SETTINGS.BUCKET_NAME
    AMAZON_S3_BASE_URL = SETTINGS.AMAZON_S3_BASE_URL
    AMAZON_S3_EUROPE_BASE_URL = SETTINGS.AMAZON_S3_EUROPE_BASE_URL



def populate_event(event_data_dict, event_to_populate, user_id):
    """return an Event instance, new event_to_populate with params
    event_data_dict, an event instance of Event
    user_id, an int from request.user.id
    """


    if event_data_dict is None:
        #user clicked on create button right after opening android screen
        return event_to_populate

    #validated mandatory data from mobile phone checked on android side
    title = event_data_dict["title"]
    description = event_data_dict["description"]
    city = event_data_dict["city"]
    category = event_data_dict["category"]
    start_date = event_data_dict["startDate"]
    is_private = event_data_dict["isPrivate"]
    address = event_data_dict["address"]
    number_invited = event_data_dict["numberInvited"]
    #is_canada will determine which AWS Bucket zone to use (north america or frankfurt zone)
    is_canada = event_data_dict["isCanada"]
    is_canada = bool(is_canada)


    #assign POST data to event
    event_to_populate.title = title
    event_to_populate.description = description
    event_to_populate.city = city
    event_to_populate.category = category
    event_to_populate.start_date = start_date
    event_to_populate.is_private = is_private
    event_to_populate.address = address
    event_to_populate.number_invited = number_invited

    #data from current user
    user = MobileUser.objects.get(id=user_id)
    event_admin_name = user.name
    event_to_populate.event_admin_name = event_admin_name
    event_admin = user.id
    event_to_populate.event_admin = event_admin

    #latitude and longitude are not mandatory
    try:
        (latitude, longitude) = event_data_dict["gps"]
        event_to_populate.latitude = latitude
        event_to_populate.longitude = longitude
        event_to_populate.cluster_id = find_my_cluster((latitude, longitude))
    except KeyError:
        pass
        #default value set in model already
    try:
        #not mandatory image
        image_stream = event_data_dict["image"]
        image_path = event_data_dict["picture_path"]
        image_path = re.split("/", image_path)[-1]
        if is_canada:
            event_to_populate.image_url = AMAZON_S3_BASE_URL+\
                str(event_to_populate.id) +"/"+str(image_path)
        else:
            event_to_populate.image_url = AMAZON_S3_EUROPE_BASE_URL+\
                str(event_to_populate.id) +"/"+str(image_path)

        if image_stream is not None:
            client = boto3.client('s3', aws_access_key_id=ACCESS_KEY,\
            aws_secret_access_key=SECRET_KEY,)

            if os.environ['COMPUTER'] == PRODUCTION_SERVERS:
                client.put_object(Key="{0}".format(BUCKET_NAME + \
                str(event_to_populate.id)+"/"+str(image_path)),\
                Body=image_stream, Bucket="events", ACL='public-read')
            else:
                client.put_object(Key="{0}".format(BUCKET_NAME + \
                str(event_to_populate.id)+"/"+str(image_path)),\
                Body=image_stream, Bucket="TEST_events", ACL='public-read')
            #image saved"
    except KeyError:
        pass
        #image will be set by default from android side depending on category
        #here send alert to email


    return event_to_populate

def find_my_cluster(my_gps):
    """my_gps is a coordinate tupple of lat, long
    return int city_cluster
    first, find closest city
    then find closest cluster in the found city
    """
    distance_world = np.zeros(len(WORLD_GPS))
    for index, gps in enumerate(WORLD_GPS):
        distance_world[index] = vincenty(my_gps, gps).km
    city_index = np.argmin(distance_world)
    city_gps = GPS_CITIES[city_index]

    distance = np.zeros(len(city_gps))
    for index, gps in enumerate(city_gps):
        distance[index] = vincenty(my_gps, gps).km
    city_cluster = np.argmin(distance)
    return city_cluster

class EventsViewSet(viewsets.ModelViewSet):
    """
    API endpoints that allows mobile phone users GET, POST events
    base_url/events and GET to check all events
    base_url/events/?{id} and GET to check an event
    base_url/events/?{city} and GET to check an event in a city
    base_url/events/?{city, cluster_id} and GET to check an
    event in a city and specific cluster ex: (montreal + UdeM)
    base_url/events/?{id} and POST + data dictionnary as parameters
    to duplicate event
    Todo merge image stream in populate_event function
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Event.objects.all()
    serializer_class = EventsSerializer
    parser_classes = (MultiPartParser, FormParser,)
    def get_queryset(self):
        """GET endpoint
        ?{id} for single instance check
        ?{clusterId, city} to check only an area of a city
        ?{is_attending, category} check my events or events I am not in,
        filtered or not by category
        """
        queryset = Event.objects.all()
        event_id = self.request.query_params.get('id', None)
        is_attending = self.request.query_params.get('isAttending', None)
        cluster_id = self.request.query_params.get('clusterId', None)
        city_index = self.request.query_params.get('cityIndex', None)
        #category int from 0 to 9, 0 is all category
        category = self.request.query_params.get('category', None)

        is_attending = bool(is_attending)
        if category is not None:
            category = int(category)

        if event_id is not None: #Todo add regex search
            event_id = re.split("/", event_id)[0]
            queryset = Event.objects.filter(event_id=int(event_id))
            return queryset

        # if(cluster_id is not None and city_index is not None):
        #     # "events in the cluster"
        #     queryset = Events.objects\
        #     .filter(event_active = True)\
        #     .filter(city = int(city_index)\
        #     .filter(cluster_id= int(cluster_id))
        #     return queryset

        if is_attending is not None and not is_attending:
            # events libres pour inscription
            #afficher pour toutes les categorys si valeur 0 (0 is all cat)
            if category is None or category == 0:
                queryset = Event.objects.exclude(event_users__id_str=self.request.user.id)\
                .filter(event_active=True)\
                .filter(city=city_index)\
                .filter(event_private=False)\
                .order_by('start_datetime')
                if cluster_id > 0:
                    queryset = queryset.filter(cluster_id=cluster_id)
                return queryset


            else:#user filtered by category

                queryset = Event.objects.exclude(event_users__id_str=self.request.user.id)\
                .filter(category=category)\
                .filter(event_active=True)\
                .filter(city=city_index)\
                .filter(event_private=False)\
                .order_by('start_datetime')
                if cluster_id > 0:
                    queryset = queryset.filter(cluster_id=cluster_id)
                return queryset

        if is_attending is not None and is_attending: #my events

            if category is None or category == 0:
                #vous demandez les events vous concernant pour toute cat"
                queryset = Event.objects\
                .filter(event_users__id_str=self.request.user.id)\
                .filter(event_active=True)\
                .filter(city=city_index)\
                .order_by('start_datetime')
                if cluster_id > 0:
                    queryset = queryset.filter(cluster_id=cluster_id)
                return queryset

            else:
                queryset = Event.objects\
                .filter(event_users__id_str=self.request.user.id)\
                .filter(event_active=True)\
                .filter(city=city_index)\
                .filter(category=category)\
                .order_by('start_datetime')
                if cluster_id > 0:
                    queryset = queryset.filter(cluster_id=cluster_id)
                return queryset




    def create(self, request):
        """POST API end points
        user can post a new event or duplicate one.
        """

        event_id_to_duplicate = self.request.query_params.get("id", None)

        is_event_duplicate = bool(event_id_to_duplicate)

        is_event_create = not is_event_duplicate
        #post_data_dict and user_id will be argument for populate an event
        post_data_dict = self.request.POST.dict()
        user_id = self.request.user.id

        if is_event_create:
            event = Event.objects.create()
        else:
            #user duplicates another s event
            event, _ = Event.objects.update_or_create(event_id=event_id_to_duplicate)

        #assign all events field in database
        event = populate_event(post_data_dict, event, user_id)
        #Todo
        #merge later image stream in populate

        serializer = EventsSerializer(event)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
