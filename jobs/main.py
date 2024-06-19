import os
from confluent_kafka import SerializingProducer
import simplejson as json
from datetime import datetime, timedelta
import random
import uuid
import time
# from iot import *

LONDON_COORDINATES = { 'latitude': 51.509865, 'longitude': -0.118092 }
BIRMINGHAM_COORDINATES = { 'latitude': 52.4869, 'longitude': -1.8905 }


# Calculate movement increments

LATITUDE_INCREMENT  = (BIRMINGHAM_COORDINATES['latitude'] - LONDON_COORDINATES['latitude']) / 100
LONGITUDE_INCREMENT = (BIRMINGHAM_COORDINATES['longitude'] - LONDON_COORDINATES['longitude']) / 100

# Environment Variable for Config

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS','localhost:9092')
VEHICLE_TOPIC = os.getenv('VEHICLE_TOPIC', 'vehicle_data')
GPS_TOPIC = os.getenv('GPS_TOPIC', 'gps_data')
TRAFFIC_TOPIC = os.getenv('TRAFFIC_TOPIC', 'traffic_data')
WEATHER_TOPIC = os.getenv('WEATHER_TOPIC', 'weather_data')
# EMERGENCY_TOPIC = os.getenv('EMERGENCY_TOPIC', 'emergency_data')

start_time = datetime.now()
start_location = LONDON_COORDINATES.copy()

###################################

random.seed(42)

def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30,60))
    return start_time

def simulate_vehicle_movement():
    global start_location
    
    start_location['latitude'] += LATITUDE_INCREMENT
    start_location['longitude'] += LONGITUDE_INCREMENT
    
    start_location['latitude'] += random.uniform(-0.0005,0.0005)
    start_location['longitude'] += random.uniform(-0.0005,0.0005)
    
    return start_location

def generate_vehicle_data(device_id):
    location = simulate_vehicle_movement()
    return {
        'id':uuid.uuid4(),
        'device_id':device_id,
        'timestamp':get_next_time().isoformat(),
        'location':(location['latitude'],location['longitude']),
        'speed':random.uniform(10,60),
        'direction':'North-East',
        'make':'BMW',
        'model':'X5',
        'year':'2024',
        'fueltype':'Petrol'
    }
    
def generate_gps_data(device_id, timestamp, speed, vehicle_type = 'private'):
    return {
        'id':uuid.uuid4(),
        'device_id':device_id,
        'timestamp':timestamp,
        'speed':speed,
        'direction':'North-East',
        'vehicle_type':vehicle_type

    }
    
def generate_traffic_camera_data(device_id, timestamp, location ,camera_id):
    return {
        'id':uuid.uuid4(),
        'device_id':device_id,
        'timestamp':timestamp,
        'location':location,
        'camera_id':camera_id,
        'snapshot': 'Base64EncodedString'
        
    }

def generate_weather_data(device_id, vehicle_data, location):
    return {
        'id':uuid.uuid4(),
        'device_id':device_id,
        'location':location,
        'timestamp':vehicle_data,
        'temperature':random.randint(-5,30),
        'weatherCondition': random.choice(['Sunny','Cloudy','Rainy']),
        'precipitation': random.uniform(0,25),
        'humidity':random.uniform(0,100),
        'windSpeed':random.uniform(0,100),
        'airQualityIndex':random.uniform(0,500)
        
    }

def json_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError('Type %s not serializable' % type(obj.__class__.__name__))


def deliver_report(err, msg):
    if err is not None:
        print('Delivery failed for User record {}: {}'.format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def produce_data_to_kafka(producer, topic, data):
    producer.produce(
        topic,
        key = str(data['id']),
        value = json.dumps(data, default= json_serializer).encode('utf-8'),
        on_delivery = deliver_report
    )
    
    producer.flush()


def simulate_journey(producer, device_id):
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data['timestamp'], speed = vehicle_data['speed'])
        traffic_camera_data = generate_traffic_camera_data(device_id, vehicle_data['timestamp'], vehicle_data['location'],'CAM-05')
        weather_data = generate_weather_data(device_id, vehicle_data['timestamp'],vehicle_data['location'])
   
        if (vehicle_data['location'][0] >= BIRMINGHAM_COORDINATES['latitude']
            and vehicle_data['location'][1] <= BIRMINGHAM_COORDINATES['longitude']):
            print("Journey completed")
            break
   
        produce_data_to_kafka(producer, VEHICLE_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)
        produce_data_to_kafka(producer, TRAFFIC_TOPIC, traffic_camera_data)
   
   
        time.sleep(5)



####################################

if __name__ == '__main__':
    producer_config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'error_cb': lambda err: print(f"KAFKA ERROR: {err}")
    }

    producer =SerializingProducer(producer_config)
    
    try:
        simulate_journey(producer, 'Vehicle-CodeWith-123')
    
    except KeyboardInterrupt:
        print('Simulation ended by the user')
    except Exception as e:
        print(f'Unexpected Error occured : {e}')
