"use strict";

var lat;
var lng;
var map = null;
var marker = null;
var sensorMarkers = [];

function aqiColorCircleIcon(aqi, color) {
    let div = document.createElement('div');
    div.style.backgroundColor = color;
    div.className = "circle-icon";
    div.innerHTML = aqi;
    return div;
}

function populateAqiMarkers(sensors) {
    // Clear old markers
    for (let i = sensorMarkers.length -1; i >= 0; i--) {
        map.removeLayer(sensorMarkers[i]);
        sensorMarkers.splice(i, 1);
    }
    // Populate new markers
    for (let i = 0; i < sensors.length; i++) {
        let aqi = Math.round(sensors[i].PM2_5Value);
        let lat = sensors[i].Lat;
        let lng = sensors[i].Lon;
        var circleIcon = L.divIcon({
            html: aqiColorCircleIcon(aqi, '#8be847')
        });
        var marker = L.marker([lat, lng], {icon: circleIcon}).addTo(map);
        sensorMarkers.push(marker);
    }
}

function updateMap(lat, lng) {
    if (map === null) {
        map = L.map('map');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }
    if (marker === null) {
        marker = L.marker([lat, lng]).addTo(map);
    }
    marker.setLatLng([lat, lng]);
    map.setView([lat, lng], 13)
}

function updateLocation(position) {
    lat = position.coords.latitude;
    lng = position.coords.longitude;
    console.log(lat);
    let location_input = document.getElementById("location_input");
    location_input.value = lat.toFixed(7) + ', ' + lng.toFixed(7);
    updateMap(lat, lng);

    // Get latest sensor data
    let url = '/api?lat=' + lat +'&long=' + lng +' &radius=2'
    fetch(url)
        .then(data=>{return data.json()})
        .then(res=>{
            populateAqiMarkers(res['data']);
        });
}

window.addEventListener('DOMContentLoaded', (event) => {
    navigator.geolocation.getCurrentPosition(updateLocation);

    let location_btn = document.getElementById("location_btn");
    location_btn.addEventListener("click", function() {
        navigator.geolocation.getCurrentPosition(updateLocation);
    });
}); 
