'''A simple server to mirror purple air data and provide queries based on distance'''

import json
import logging
import logging.handlers
from math import *
from multiprocessing.connection import Listener
import requests
import threading
import time
import traceback

from apscheduler.schedulers.background import BackgroundScheduler

SERVER_ADDRESS = ('localhost', 6000)
PURPLE_AIR_API = 'https://www.purpleair.com/json'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] %(message)s",
    handlers = [
        logging.handlers.RotatingFileHandler(
            'logs/purpleair_proxy.log',
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger()

class PurpleAirProxy:
    def __init__(self):
        self.data = []
        self.data_lock = threading.Lock()

    def _fast_distance(self, lat1, long1, lat2, long2):
        R = 6371 # radius of the earth in km
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        long1 = radians(long1)
        long2 = radians(long2)
        x = lat2 - lat1
        y = (long2 - long1)*cos(0.5*(lat2+lat1))
        return R*sqrt(x*x + y*y)

    def _find_nearest_sensors(self, lat, long, radius):
        #TODO: Speed up with numpy
        with self.data_lock:
            results = []
            for d in self.data:
                distance = self._fast_distance(lat, long, d['Lat'], d['Lon'])
                if distance < radius:
                    results.append(d)
        return results

    
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
                                    request['long'],
                                    request['radius'])
                        end_time = time.time()

                        log.info('Calculation time: ' + str(end_time-start_time))

                        conn.send(nearest_sensors)
                except Exception as e:
                    # We want this server to stay alive always if possible, so just log and move on
                    log.error(traceback.format_exc())
    
    def refresh_data(self):
        log.info("Refreshing data...")

        r = requests.get(PURPLE_AIR_API)
        if r.status_code == 200:
            try:
                new_data = json.loads(r.text)
            except ValueError: 
                # Purple Air sometimes just craps out and cuts off their json response.
                # I'm pretty sure this is a bug on their end. Not much to do except log it and move on.
                text = (r.text[:1000] + '\n...') if len(r.text) > 1000 else r.text
                log.warning("Bad json response:\n" + text)
                return

            new_data = new_data['results']

            # Filter out bad sensors. Some are missing fields
            new_data = filter(
                lambda d: (
                    d.get('DEVICE_LOCATIONTYPE', None) == 'outside' and
                    'Lat' in d and
                    'Lon' in d
                ),
                new_data
            ) 

            with self.data_lock:
                self.data = list(new_data)

            log.info("Refresh successful")
        else:
            log.error("Error! Bad response from purpleair (" + str(r.status_code) + "):\n" + r.text)


def main():
    log.info('Starting new run...')

    server = PurpleAirProxy()

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(
        lambda server: server.refresh_data(),
        'interval',
        [server],
        minutes=1
    )
 
    sched.start()

    server.refresh_data()
    server.run()
    

if __name__ == '__main__':
    main()
