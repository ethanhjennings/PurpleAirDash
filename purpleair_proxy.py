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
from apscheduler.executors.pool import ThreadPoolExecutor
import numpy as np

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
        self.data = None
        # Lats and longs refers to numpy arrays built in refresh_data
        self.lats = None
        self.longs = None
        self.data_lock = threading.Lock()

    def _find_nearest_sensors(self, lat, long, radius):
        if self.data == None:
            return None
        
        with self.data_lock:
            R = 6371 # radius of the earth in km
            cur_lat, cur_long = np.radians(lat), np.radians(long)
            rad_lats, rad_longs = np.radians(self.lats), np.radians(self.longs)
            a = np.subtract(rad_lats, cur_lat)
            b = np.subtract(rad_longs, cur_long)
            c = np.multiply(np.add(rad_lats, cur_lat), 0.5)
            d = np.cos(c)
            e = np.multiply(d, b)
            f = np.add(np.power(a, 2), np.power(e, 2))
            g = np.multiply(np.sqrt(f), R)

        return [self.data[sensor] for sensor in np.where(g<radius)[0].tolist()]
    
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
                        log.info('Num sensors returned: ' + str(len(nearest_sensors) if nearest_sensors is not None else 0))

                        if nearest_sensors is not None:
                            conn.send({'data': nearest_sensors, 'status': 'ok'})
                        else:
                            conn.send({'status': 'failure'})
                except Exception as e:
                    # We want this server to stay alive always if possible, so just log and move on
                    log.error(traceback.format_exc())

    def _clean_data(self, data):

        # Every sensor has two channels, A and B. B channels are specified separately
        # and are only linked with a " B" at the end of the label. So we need to
        # merge the B's into the A's

        # Strip out unused fields
        used_keys = ['Label', 'Lat', 'Lon', 'Flag', 'Stats', 'AGE', 'A_H', 'DEVICE_LOCATIONTYPE']
        data = [{k: v for k, v in d.items() if k in used_keys} for d in data]

        # Remove extra whitespace which is messing up correlating A and B sensors
        for d in data:
            d['Label'] = ' '.join(d['Label'].strip().split())

        data_map = {d['Label']: d for d in data}

        new_data = []
        for label, d in list(data_map.items()):
            is_b_sensor = label.endswith(' B') or label.endswith(' P2')
            if is_b_sensor:
                if label.endswith(' P2'):
                    a_label = label[:-1] + '1'
                else:
                    a_label = label[:label.rfind(' ')]
                if a_label in data_map:
                    data_map[a_label]['b_sensor'] = d
                    del data_map[label]

        # Filter out bad sensors
        new_data = list(filter(
            lambda d: (
                d.get('DEVICE_LOCATIONTYPE', None) == 'outside' and
                    # Ensure sensor is inside
                d.get('Flag', None) != 1 and d['b_sensor'].get('Flag', None) != 1 and
                    # Ensure not flagged for bad readings
                d.get('A_H', None) != True and d['b_sensor'].get('A_H', None) != True and
                    # Ensure not flagged for bad hardware
                d.get('AGE', 99999) < 10 and d['b_sensor'].get('AGE', 99999) < 10 and
                    # Make sure the data is fresh
                'Stats' in d and 'Stats' in d['b_sensor'] and
                    # Make sure the data is fresh
                'Lat' in d and
                'Lon' in d
                    # Ensure it has a known location
            ),
            data_map.values()
        ))

        return new_data
    
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
            log.info("Got " + str(len(new_data)) + " sensors")
            new_data = self._clean_data(new_data)

            with self.data_lock:
                self.data = new_data
                self.lats = np.array([sensor['Lat'] for sensor in self.data])
                self.longs = np.array([sensor['Lon'] for sensor in self.data])

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
