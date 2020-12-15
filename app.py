from multiprocessing.connection import Client
from flask import Flask, send_from_directory, g, request, jsonify, abort, redirect
import json
import time
import requests
from math import *

app = Flask(__name__)

@app.route('/')
def aqi():
    return app.send_static_file('index.html')

@app.route('/api', methods=['GET'])
def api():
    lat = request.args.get('lat', type=float)
    if lat is None:
        return jsonify(status="error", message="Missing lat url argument"), 400

    lon = request.args.get('lon', type=float)
    if lon is None:
        return jsonify(status="error", message="Missing lon url argument"), 400

    radius = request.args.get('radius', type=float)
    if radius is None:
        return jsonify(status="error", message="Missing radius url argument"), 400

    try:
        with Client(('localhost', 6000)) as conn:
            conn.send({
                'lat': lat,
                'lon': lon,
                'radius': radius
            })
            results = conn.recv()
            if results.get('status', None) != 'ok':
                return jsonify(status="error", message="Bad response from purple air proxy"), 502
    except ConnectionRefusedError:
        return jsonify(status="error", message="Unable connect to purple air proxy"), 502

    return jsonify(data=results['data'], status="ok")

@app.route('/<path:filename>')
def send_js(filename):
    return send_from_directory('static/', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, ssl_context='adhoc')
