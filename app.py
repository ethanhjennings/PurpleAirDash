from multiprocessing.connection import Client
from flask import Flask, send_from_directory, g, request, jsonify, abort, redirect
import json
import time
import requests
from math import *

app = Flask(__name__)

def pm25_to_aqi(pm25_concentration):
    epa_pm25 = [
        (0.0,   12.0),
        (12.1,  35.4),
        (35.5,  55.4),
        (55.5,  150.4),
        (150.5, 250.4),
        (250.5, 350.4),
        (350.5, 500.4)   
    ]
    epa_aqi = [
        (0,   50),
        (51,  100),
        (101, 150),
        (151, 200),
        (201, 300),
        (301, 400),
        (401, 500),
    ]

    if pm25_concentration > 500.4:
        return 500

    if pm25_concentration < 0:
        return 0

def fast_distance(lat1, long1, lat2, long2):
    R = 6371 # radius of the earth in km
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    long1 = radians(long1)
    long2 = radians(long2)
    x = lat2 - lat1
    y = (long2 - long1)*cos(0.5*(lat2+lat1))
    return R*sqrt(x*x + y*y)

@app.route('/')
def root():
    return redirect("https://github.com/ethanhjennings")

@app.route('/aqi')
def aqi():
    return app.send_static_file('index.html')

@app.route('/aqi/api', methods=['GET'])
def api():
    lat = request.args.get('lat', type=float)
    long = request.args.get('long', type=float)
    radius = request.args.get('radius', type=float)
    start = time.time()
    with Client(('localhost', 6000)) as conn:
        conn.send({
            'lat': lat,
            'long': long,
            'radius': radius
        })
        data = conn.recv()
        end = time.time()
    return jsonify(data=data, time=end-start)

@app.route('/js/<path:filename>')
def send_js(filename):
    app.logger.info(filename)
    return send_from_directory('static/js', filename)

@app.route('/css/<path:filename>')
def send_css(filename):
    app.logger.info(filename)
    return send_from_directory('static/css', filename)

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=443, ssl_context=(
        '/etc/letsencrypt/live/ethanj.me/fullchain.pem',
        '/etc/letsencrypt/live/ethanj.me/privkey.pem'
    ))
