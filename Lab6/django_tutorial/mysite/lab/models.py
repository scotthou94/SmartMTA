# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class City(models.Model):
    lookup_time = models.DateTimeField()
    city_name = models.CharField(max_length=128)
    temperature = models.IntegerField(default=666)
