from django.db import models
from User.model import User
from django.db.models import (Model, TextField, DateTimeField, ForeignKey,CASCADE)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer



class Message(models.Model):
    """
       This class represents a chat message. It has a owner (user), timestamp and
       the message body.
    """
    user = ForeignKey(User, on_delete = CASCADE , verbose_name = 'user', related_name = 'to_user', db_index = True)
    recipient = ForeignKey(User, on_delete = CASCADE, verbose_name = 'user', related_name = 'to_user', db_index = True)
    timestamp = DateTimeField('timestamp', auto_now_add = True, editable = False, db_index = True)
    body = TextField('body')

    def __str__(self):
        return str(self.id)

    def characters(self):
        return len(self.body)








    #class Room(models.Model):
        label = models.SlugField(unique=True)
        receiver = models.ForeignKey(User, related_name="receiver")
        sender = models.ForeignKey(User, related_name="sender")
