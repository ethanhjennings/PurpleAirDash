'''A simple server to mirror purple air data and provide queries based on distance'''

import json
import logging
import logging.handlers
from math import *
from statistics import mean
from multiprocessing.connection import Listener
import requests
import threading
import time
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import numpy as np

import aqi

SERVER_ADDRESS = ('localhost', 6000)

API_URL = 'https://api.purpleair.com/v1/sensors'
API_FIELDS = ['sensor_index', 'name', 'location_type', 'latitude', 'longitude', 'confidence', 'pm2.5_10minute']
SENSOR_MAX_AGE = 60*10 # We want the 10 minute average so longer than that could mess with readings

with open('api_key.txt') as f:
    API_KEY = f.read().strip()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] %(message)s",
    handlers = [
        logging.handlers.RotatingFileHandler(
            'logs/purpleair_proxy/purpleair_proxy.log',
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger()

class PurpleAirProxy:
    def __init__(self):
        self.data = None
        # lats and lons refers to numpy arrays built in refresh_data
        self.lats = None
        self.lons = None
        self.data_lock = threading.Lock()
        self.last_modified = time.time()

    def _find_nearest_sensors(self, lat, lon, radius):
        if self.data == None:
            return None
        
        with self.data_lock:
            R = 6371 # radius of the earth in km
            cur_lat, cur_lon = np.radians(lat), np.radians(lon)
            rad_lats, rad_lons = np.radians(self.lats), np.radians(self.lons)
            lat_diffs = np.subtract(rad_lats, cur_lat)
            lon_diffs = np.subtract(rad_lons, cur_lon)
            lat_midpoints = np.multiply(np.add(rad_lats, cur_lat), 0.5)
            midpoints_cos = np.cos(lat_midpoints)
            midpoint_lon_products = np.multiply(midpoints_cos, lon_diffs)
            squared_latlon_sums = np.add(np.power(lat_diffs, 2), np.power(midpoint_lon_products, 2))
            sensor_distances = np.multiply(np.sqrt(squared_latlon_sums), R)

        return [self.data[sensor] for sensor in np.where(sensor_distances<radius)[0].tolist()]

    def run(self):
        log.info('Listening for connections...')
        #TODO: Multithreaded connection handling?
        with Listener(SERVER_ADDRESS) as listener:
            while True:
                try:
                    with listener.accept() as conn:
                        log.info('Connection accepted from ' + str(listener.last_accepted))
                        request = conn.recv()
                        log.info('Incoming request data: ' + str(request))
                
                        start_time = time.time()
                        nearest_sensors = self._find_nearest_sensors(
                                    request['lat'],
                                    request['lon'],
                                    request['radius'])
                        end_time = time.time()

                        log.info('Calculation time: ' + str(end_time-start_time))
                        log.info('Num sensors returned: ' + str(len(nearest_sensors) if nearest_sensors is not None else 0))

                        if len(nearest_sensors) == 0:
                            conn.send({
                                'pm2.5': None,
                                'aqi': None,
                                'color': None,
                                'level': None,
                                'message': None,
                                'last_modified': self.last_modified,
                                'status': 'ok',
                                'sensors': [],
                            })
                            continue

                        avg_pm25 = mean(s['pm2.5'] for s in nearest_sensors)
                        avg_aqi = aqi.from_pm25(avg_pm25)
                        message = aqi.to_message(avg_aqi)
                        color = aqi.to_color(avg_aqi)

                        if nearest_sensors is not None:
                            conn.send({
                                'pm2.5': avg_pm25,
                                'aqi': avg_aqi,
                                'color': color,
                                'level': message['level'],
                                'message': message['message'],
                                'last_modified': self.last_modified,
                                'status': 'ok',
                                'sensors': nearest_sensors,
                            })
                        else:
                            conn.send({'status': 'failure'})
                except Exception as e:
                    # We want this server to stay alive always if possible, so just log and move on
                    log.error(traceback.format_exc())

    def refresh_data(self):
        log.info("Refreshing data...")

        r = requests.get(
            API_URL,
            params = {
                'fields': ','.join(API_FIELDS),
                'max_age': SENSOR_MAX_AGE
            },
            headers = {
                'X-API-Key': API_KEY
            }
        )
        if r.status_code == 200:
            try:
                json_response = json.loads(r.text)
            except ValueError: 
                # Purple Air sometimes just craps out and cuts off their json response.
                # I'm pretty sure this is a bug on their end. Not much to do except log it and move on.
                text = (r.text[:1000] + '\n...') if len(r.text) > 1000 else r.text
                log.warning("Bad json response:\n" + text)
                return

            new_data = json_response['data']
            field_idx = {f: i for i,f in enumerate(json_response['fields'])}
            log.info("Got " + str(len(new_data)) + " sensors")

            # Filter out bad sensors
            new_data = [
                d for d in new_data if (
                    # Ensure sensor is outside
                    d[field_idx['location_type']] == 0 and

                    # Ensure confidence is not too low
                    d[field_idx['confidence']] >= 25 and

                    # Ensure we have all fields
                    d[field_idx['latitude']] is not None and
                    d[field_idx['longitude']] is not None and
                    d[field_idx['longitude']] is not None and
                    d[field_idx['pm2.5_10minute']] is not None
                )
            ]

            log.info("Got " + str(len(new_data)) + " sensors after cleaning")

            # Convert to sensor format and pre-calculate values
            new_data = [
                {
                    'name': d[field_idx['name']],
                    'lat': float(d[field_idx['latitude']]),
                    'lon': float(d[field_idx['longitude']]),
                    'pm2.5': (pm25 := float(d[field_idx['pm2.5_10minute']])),
                    'aqi': (aqi_v := aqi.from_pm25(pm25)),
                    'color': aqi.to_color(aqi_v)
                }
                for d in new_data
            ]

            with self.data_lock:
                self.data = new_data
                self.lats = np.array([sensor['lat'] for sensor in self.data])
                self.lons = np.array([sensor['lon'] for sensor in self.data])

            self.last_modified = time.time()
            log.info("Refresh successful")
        else:
            log.error("Error! Bad response from purpleair (" + str(r.status_code) + "):\n" + r.text)


def main():
    log.info('Starting new run...')

    server = PurpleAirProxy()

    sched = BackgroundScheduler(daemon=True, executors= {
        'threadpool': ThreadPoolExecutor(max_workers=1),
         # This seems to fix a memory leak? why???
    })
    sched.add_job(
        lambda server: server.refresh_data(),
        'interval',
        [server],
        minutes=1,
        executor='threadpool' # Also for the memory leak?
    )

    server.refresh_data()
    sched.start()
    server.run()
    

if __name__ == '__main__':
    main()
