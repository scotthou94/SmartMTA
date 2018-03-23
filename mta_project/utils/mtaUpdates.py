'''
Group: x007
Murshed Jamil Ahmed (mja2196)
Shijun Hou (sh3658)
Jiahong He (jh3863)
Robert Fea (rf2638)
IoT Lab 3: mtaUpdates.py
'''

import urllib2
import contextlib
from datetime import datetime
from collections import OrderedDict
from collections import defaultdict

from pytz import timezone
import gtfs_realtime_pb2
import google.protobuf

import vehicle, alert, tripupdate

class mtaUpdates(object):

    # Do not change Timezone
    TIMEZONE = timezone('America/New_York')
    
    # feed url depends on the routes to which you want updates
    # here we are using feed 1 , which has lines 1,2,3,4,5,6,S
    # While initializing we can read the API Key and add it to the url
    feedurl = 'http://datamine.mta.info/mta_esi.php?feed_id=1&key='
    
    VCS = {1:"INCOMING_AT", 2:"STOPPED_AT", 3:"IN_TRANSIT_TO"}    
    tripUpdates = []
    alerts = []

    # header timestamp value
    timestamp = 0

    def __init__(self,apikey):
        self.feedurl = self.feedurl + apikey
        print self.feedurl

    # Method to get trip updates from mta real time feed
    def getTripUpdates(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        try:
            with contextlib.closing(urllib2.urlopen(self.feedurl)) as response:
                d = feed.ParseFromString(response.read())
        except (urllib2.URLError, google.protobuf.message.DecodeError) as e:
            print "Error while connecting to mta server " +str(e)

        timestamp = feed.header.timestamp
        print "Timestamp: ", timestamp
        nytime = datetime.fromtimestamp(timestamp, self.TIMEZONE)
        print "NYC Time: ", nytime

        self.timestamp = timestamp
        self.tripUpdates = []
        self.alerts = []

        for entity in feed.entity:
            # Trip update represents a change in timetable
            if entity.trip_update and entity.trip_update.trip.trip_id:
                # Assign the tripupdate fields
                t = tripupdate.tripupdate()
                t.tripId = entity.trip_update.trip.trip_id
                t.routeId = entity.trip_update.trip.route_id
                t.startDate = entity.trip_update.trip.start_date
                t.direction = entity.trip_update.trip.direction_id

                # There can be many StopTimeUpdate messages
                for st_update in entity.trip_update.stop_time_update:
                    times = []
                    times.append({"arrivalTime": st_update.arrival.time})
                    times.append({"departureTime": st_update.departure.time})
                    t.futureStops[st_update.stop_id] = times

                self.tripUpdates.append(t)

            if entity.vehicle and entity.vehicle.trip.trip_id:
                v = vehicle.vehicle()
                v.currentStopNumber = entity.vehicle.current_stop_sequence
                v.currentStopId = entity.vehicle.stop_id
                v.timestamp = entity.vehicle.timestamp
                v.currentStopStatus = entity.vehicle.current_status

                # Using the trip_id on a vehicle, associate that vehicle with the trip update object
                vehicleTripId = entity.vehicle.trip.trip_id
                self.setVehicleDataOnTripUpdate(vehicleTripId, v)

            if entity.HasField('alert') and entity.alert:
                a = alert.alert()
                a.alertMessage = entity.alert.header_text.translation[0].text
                for informed_entity in entity.alert.informed_entity:
                    tripId = informed_entity.trip.trip_id
                    a.tripId.append(tripId)
                    a.routeId[tripId] = informed_entity.trip.route_id
                    a.startDate[tripId] = informed_entity.trip.start_time
                self.alerts.append(a)

        return self.tripUpdates
    
    # END OF getTripUpdates method

    def setVehicleDataOnTripUpdate(self, tripId, vehicleData):
        """
        Loop over the trip update objects and set the vehicleData field for any tripupdate with a matching tripId.
        :param tripId: The vehicle's tripId
        :param vehicleData: The matching vehicle object
        :return: None
        """
        # loop over trip updates and set the vehicle ID on any trip update with a matching trip ID
        for idx in range(len(self.tripUpdates)):
            if self.tripUpdates[idx].tripId == tripId:
                self.tripUpdates[idx].vehicleData = vehicleData

    def getOrderedDictOfTripUpdate(self, tu):
        """
        Convert a tripupdate object to an ordered dictionary with all the required fields for database storage.
        :param tu: An instance of the tripupdate class
        :return: OrderedDict
        """
        d = OrderedDict()
        d['tripId'] = tu.tripId
        d['routeId'] = tu.routeId
        d['startDate'] = tu.startDate
        d['direction'] = tu.direction

        # Extract the trip direction (N or S) from the tripId
        if d['tripId']:
            d['direction'] = d['tripId'][10]

        d['currentStopId'] = 0
        d['currentStopStatus'] = 0
        d['vehicleTimeStamp'] = 0
        if tu.vehicleData:
            if hasattr(tu.vehicleData, 'currentStopId'):
                d['currentStopId'] = tu.vehicleData.currentStopId
            if hasattr(tu.vehicleData, 'currentStopStatus'):
                stopStatus = tu.vehicleData.currentStopStatus
                if self.VCS.has_key(stopStatus):
                    d['currentStopStatus'] = self.VCS[stopStatus]
            if hasattr(tu.vehicleData, 'timestamp'):
                d['vehicleTimeStamp'] = tu.vehicleData.timestamp

        d['futureStopData'] = tu.futureStops
        d['timestamp'] = self.timestamp
        return d

