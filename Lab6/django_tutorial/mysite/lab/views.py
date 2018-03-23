# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import City
from django.utils import timezone
from weather import Weather
from weather import Unit
import googlemaps
import datetime
import json
import polyline
from django.http import JsonResponse

from gmplot import gmplot

weather = Weather(Unit.FAHRENHEIT)
gmaps = googlemaps.Client(key='AIzaSyDNdMn3S1cRojULLiWFdNXosKSIyOnNFvo')

# Create your views here.
def index(request):
    # return HttpResponse('This is the home page of Lab 6')
    template = loader.get_template('lab/index.html')
    header = 'It is ' + datetime.datetime.now().strftime('%B %d, %Y at %I:%M:%S %p ')
    context = {'header': header}
    return HttpResponse(template.render(context, request))

def edisonTemp(request):
    temperature = getEdisonTemerature()
    response = {
        'time': datetime.datetime.now().strftime('%I:%M:%S'),
        'temperature': temperature
    }
    return JsonResponse(response)

def chart(request):
    template = loader.get_template('lab/chart.html')
    context = {}
    return HttpResponse(template.render(context, request))

def temperature(request):
    sourceCity = request.POST['source_city']
    destinationCity = request.POST['destination_city']

    sourceCityTemp = getTemperatureByCity(sourceCity)
    saveCityToDb(sourceCity, sourceCityTemp)
    destinationCityTemp = getTemperatureByCity(destinationCity)
    saveCityToDb(destinationCity, destinationCityTemp)

    template = loader.get_template('lab/temperature.html')
    directions = getDirections(sourceCity, destinationCity)
    filePath = createMap(directions)
    context = {
        'source_city': sourceCity,
        'destination_city': destinationCity,
        'source_city_temp': sourceCityTemp,
        'destination_city_temp': destinationCityTemp,
        'map_file_path': filePath,
    }
    return HttpResponse(template.render(context, request))

def showMap(request):
    template = loader.get_template('lab/map_render.html')
    return HttpResponse(template.render({}, request))

def saveCityToDb(cityName, temperature):
    # Add to the database
    c = City(lookup_time=timezone.now(), city_name=cityName, temperature=temperature)
    c.save()

def getTemperatureByCity(cityName):
    location = weather.lookup_by_location(cityName)
    condition = location.condition()
    return condition.temp()

def getDirections(sourceCity, destinationCity):
    result = gmaps.directions(sourceCity, destinationCity)
    # return json.dumps(result, indent=4, sort_keys=True)
    return result

def createMap(directions):
    # Place map
    journey = directions[0]
    leg = journey['legs'][0]
    startLat = leg['start_location']['lat']
    startLng = leg['start_location']['lng']
    gmap = gmplot.GoogleMapPlotter(startLat, startLng, 8, 'AIzaSyDy3n-APz8IwQL3AaOwcEN27S5_R3BRQ-g')

    points = polyline.decode(journey['overview_polyline']['points'])

    latitudes, longitudes = zip(*points)
    gmap.plot(latitudes, longitudes, 'red', edge_width=5)

    # Draw
    filename = 'lab/templates/lab/map_render.html'
    gmap.draw(filename)
    return filename

def getEdisonTemerature():
    # TODO: Actual temperature sensor reading
    # This is just a stub to get it running
    import random
    return random.randint(1, 100)
