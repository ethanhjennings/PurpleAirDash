from multiprocessing.connection import Client
from flask import Flask, send_from_directory, g, request, jsonify, abort, redirect
import json
import time
import requests
from math import *

app = Flask(__name__)

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
    app.run(host='0.0.0.0')
