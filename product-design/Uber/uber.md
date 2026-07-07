## Functional requirements
- Users able request fare for a ride by providing pickup and dropoff locations
- Users able request a ride by providing pickup and dropoff locations
- Upon request, riders should be matched with a driver who is nearby and available.
- Drivers able to accept or reject ride requests
- Drivers able to start and end rides

## out of scope Functiona Requirements
- Drivers able to rate rides
- Users able to rate rides
- Users able to cancel rides
- Just one car type

## Non-functional requirements
- Low latency to match rider and driver, less then 1 minutes
- Storing consistency for dirver accpeting the ride
- Should able handle 1000 requests per second during events from a same location

## core entities
- Rider
- Driver
- Ride
- GeoLocation

## API

POST v1/Rides/checkFare
{
    source:
    destination:
}

Response Ride - Partial object

{
    ride_id:
    estimated_fare:
    status: checkFare
}
Request Ride - Book Ride

POST v1/rides/{id}

Ride
{
 ride_id:
 source:
 destination:
 estimated_fare:
 driver_id:
 status: booked
}

- Driver persona
update location

Post drivers/{id}/locations
{
    lat:
    long:
}

Accept or reject Ride

PATCH v1/rides/{id}
{
    accept/deny
}

## Highe level System Design


