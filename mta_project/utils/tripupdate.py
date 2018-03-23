from collections import OrderedDict


# Storing trip related data
# Note : some trips wont have vehicle data
class tripupdate(object):
    def __init__(self):
        # From TripDescriptor message
        self.tripId = None
        self.routeId = None
        self.startDate = None
        self.direction = None

        # From VehicleDescriptor message
        self.vehicleData = None

        # From StopTimeUpdate message
        self.futureStops = OrderedDict()  # Format {stopId : [arrivalTime,departureTime]}
