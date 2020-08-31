"use strict";

var lat = null;
var lng = null;
var map = null;
var marker = null;
var sensorMarkers = [];
var radius = 2;
var correction_type = "none";

function aqiColorCircleIcon(aqi, color, text_color) {
    let div = document.createElement('div');
    div.style.backgroundColor = color;
    div.style.color = text_color;
    div.className = "circle-icon";
    div.innerHTML = aqi;
    return div;
}

function clearMarkers() {
    // Clear old markers
    for (let i = 0; i < sensorMarkers.length; i++) {
        map.removeLayer(sensorMarkers[i]);
    }
    sensorMarkers = [];
}

function populateAqiMarkers(sensors) {
    // Populate new markers
    for (let i = 0; i < sensors.length; i++) {
        let aqi = Math.round(sensors[i].aqi);
        let lat = sensors[i].lat;
        let lng = sensors[i].lng;
        var circleIcon = L.divIcon({
            html: aqiColorCircleIcon(aqi, aqiToColor(aqi), aqiToTextColor(aqi))
        });
        var marker = L.marker([lat, lng], {icon: circleIcon}).addTo(map);
        sensorMarkers.push(marker);
    }
}

function sensorsToAqi(sensors, timeframe) {
    let total_pm25 = 0;
    let aqis = [];
    for (let i = 0; i < sensors.length; i++) {
        let a_stats = JSON.parse(sensors[i].Stats);
        let b_stats = JSON.parse(sensors[i].b_sensor.Stats);
        let pm25_a = parseFloat(a_stats[timeframe]);
        let pm25_b = parseFloat(b_stats[timeframe]);
        let pm25 = (pm25_a + pm25_b)/2;

        if (correction_type === "lrapa") {
            pm25 = Math.max(0.5 * pm25 - 0.66, 0);
        } else if (correction_type === "aqandu") {
            pm25 = 0.778 * pm25 + 2.65;
        }

        total_pm25 += pm25;

        let aqi = pm25ToAQI(pm25);
        aqis.push(
            {aqi: aqi, lat: sensors[i].Lat, lng: sensors[i].Lon}
        );
    }
    return {
        aqis: aqis,
        mean_aqi: pm25ToAQI(total_pm25/aqis.length)
    };
}

function updateMap(lat, lng, zoom) {
    if (map === null) {
        map = L.map('map');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        map.setView([lat, lng], 13);
    }
    if (marker === null) {
        marker = L.marker([lat, lng]).addTo(map);
    }
    marker.setLatLng([lat, lng]);

    if (zoom) {
        // Set view to show all markers
        var group = new L.featureGroup(sensorMarkers.concat(marker));
        map.fitBounds(group.getBounds(), {padding: L.point(40, 40)});
    }
}

function updateAQIBox(sensors) {
    let results = sensorsToAqi(sensors, 'v1');
    clearMarkers();
    populateAqiMarkers(results.aqis);

    let aqi_info = aqiToInfo(results.mean_aqi);

    let aqi_box = document.getElementById("aqi-display-box");
    let aqi_value_box = document.getElementById("aqi-value-box");
    let aqi_div = document.getElementById("aqi-value");
    let aqi_level_div = document.getElementById("aqi-level");
    let aqi_message_div = document.getElementById("aqi-message");

    aqi_level_div.classList.remove("transition");
    aqi_message_div.classList.remove("transition");

    if (results.aqis.length !== 0) {
        aqi_box.style.backgroundColor = aqiToColor(results.mean_aqi);
        aqi_box.style.color = aqiToTextColor(results.mean_aqi);
        aqi_value_box.style.borderColor = aqiToTextColor(results.mean_aqi);
        aqi_div.innerHTML = results.mean_aqi;
        aqi_level_div.innerHTML = aqi_info.level;
        aqi_message_div.innerHTML = aqi_info.message;
    } else {
        aqi_box.style.backgroundColor = "#cccccc";
        aqi_box.style.color = "#222222";
        aqi_value_box.style.borderColor = "#222222";
        aqi_div.innerHTML = "--";
        aqi_level_div.innerHTML = "No Data";
        aqi_message_div.innerHTML = "There's no data available at this location and range. Try expanding the range option.";
    }
}

function updateLocation(position) {
    if (lat !== null && lng !== null &&
        position.coords.latitude.toFixed(7) === lat.toFixed(7) && 
        position.coords.longitude.toFixed(7) === lng.toFixed(7)) {
        // No change, so no need to re-query and render everything
        return;
    }
    lat = position.coords.latitude;
    lng = position.coords.longitude;
    let location_input = document.getElementById("location_input");
    location_input.value = lat.toFixed(7) + ', ' + lng.toFixed(7);
    refreshData();
}

function refreshData() {
    clearMarkers();
    updateMap(lat, lng, false);

    // Get latest sensor data
    let url = 'api?lat=' + lat +'&long=' + lng +' &radius=' + radius;
    fetch(url)
        .then(data=>{return data.json()})
        .then(res=>{
            updateAQIBox(res['data']);
            updateMap(lat, lng, true);
        });
    
}

function parseLatLong(str) {
    const re = /(-?\d*\.?\d*)\s*,\s*(-?\d*\.?\d*)/
    let match = str.match(re);
    if (match !== null && match.length === 3) {
        return [parseFloat(match[1]), parseFloat(match[2])];
    } else {
        return null;
    }
}

window.addEventListener('DOMContentLoaded', (event) => {
    let location_btn = document.getElementById("location_btn");
    location_btn.addEventListener("click", function() {
        navigator.geolocation.getCurrentPosition(updateLocation);
    });

    let location_input = document.getElementById("location_input");
    const handleInputEvent = (event) => {
        let lat_long = parseLatLong(location_input.value);
        if (lat_long !== null) {
            updateLocation({
                coords:  {latitude: lat_long[0], longitude: lat_long[1]}
            });
        }
    };
    location_input.addEventListener("blur", handleInputEvent);
    location_input.addEventListener("keyup", (event) => {
        if (event.keyCode === 13) {
            event.preventDefault();
            handleInputEvent();
        }
    });

    let radius_select = document.getElementById("radius");
    let stored_radius = window.localStorage.getItem('radius');
    if (stored_radius !== null) {
        radius = stored_radius;
        radius_select.value = stored_radius;
    }
    radius_select.addEventListener('change', (event) => {
        radius = parseFloat(event.target.value); 
        window.localStorage.setItem('radius', radius);
        refreshData();
    });

    let correction_select = document.getElementById('correction');
    let stored_correction = window.localStorage.getItem('correction');
    if (stored_correction !== null) {
        correction_type = stored_correction;
        correction_select.value = stored_correction;
    }
    correction_select.addEventListener('change', (event) => {
        correction_type = event.target.value;
        window.localStorage.setItem('correction', correction_type);
        refreshData();
    });

    navigator.geolocation.getCurrentPosition(updateLocation);

    // Hack to get :active css selector working on mobile
    document.addEventListener("touchstart", function() {}, true);
}); 
