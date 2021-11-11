"use strict";

var lat = null;
var lng = null;
var lat_lng_str = null;
var map = null;
var marker = null;
var sensorMarkers = [];
var radius = 2;
var correction_type = "none";
var auto_complete;
var autocomplete_timestamp = 0;

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

function sensorsToAqi(sensors) {
    let total_pm25 = 0;
    let aqis = [];
    for (let i = 0; i < sensors.length; i++) {
        let pm25 = sensors[i]['pm2.5'];

        if (correction_type === "lrapa") {
            pm25 = Math.max(0.5 * pm25 - 0.66, 0);
        } else if (correction_type === "aqandu") {
            pm25 = 0.778 * pm25 + 2.65;
        }

        total_pm25 += pm25;

        let aqi = pm25ToAQI(pm25);
        aqis.push(
            {aqi: aqi, lat: sensors[i].lat, lng: sensors[i].lon}
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
    let results = sensorsToAqi(sensors);
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

function updateLocation(position, address) {
    lat = position.coords.latitude;
    lng = position.coords.longitude;
    lat_lng_str = lat.toFixed(5) + ', ' + lng.toFixed(5);
    let location_input = document.getElementById("location_input");
    if (typeof address !== 'undefined') {
        location_input.value = address;
    } else {
        location_input.value = lat_lng_str;
    }
    refreshData();
}

function refreshData() {
    clearMarkers();
    updateMap(lat, lng, false);

    // Get latest sensor data
    let url = 'api?lat=' + lat +'&lon=' + lng +' &radius=' + radius;
    fetch(url)
        .then(data=>data.json())
        .then(res=>{
            updateAQIBox(res['sensors']);
            updateMap(lat, lng, true);
            updateURLFragment();
        });
}

function parseLatLong(str) {
    const re = /(?<lat>-?\d*\.?\d*)°?\s*(?<lat_dir>N|S)?\s*,?\s*(?<lng>-?\d*\.?\d*)\s*°?\s*(?<lng_dir>W|E)?/g;
    const match = re.exec(str);
    if (match !== null && match.groups.lat && match.groups.lng) {
        let lat = parseFloat(match.groups.lat);
        let lng = parseFloat(match.groups.lng);
        if (match.groups.lat_dir && match.groups.lat_dir === "S") {
            lat *= -1;
        }
        if (match.groups.lng_dir && match.groups.lng_dir === "W") {
            lng *= -1;
        }
        return [lat, lng];
    } else {
        return null;
    }
}

function updateURLFragment() {
  const location = lat_lng_str;
  const radius = document.getElementById('radius').value;
  const correction = document.getElementById('correction').value;

  const params = new URLSearchParams({location, radius, correction});
  const fragment = '#' + params.toString();
  window.history.replaceState(null, '', fragment);
}

function parseURLFragment() {
    const obj = {};

    const fragment = window.location.hash.substring(1);
    const params = new URLSearchParams(fragment);

    ['radius', 'location', 'correction'].forEach(key => {
        if (params.has(key)) {
            obj[key] = params.get(key);
        }
    });

    return obj;
}

let entrypoint = document.currentScript.getAttribute('data-entrypoint');
if (entrypoint === "main") {
    window.addEventListener('DOMContentLoaded', (event) => {
        const {
            radius: url_radius,
            location: url_location,
            correction: url_correction,
        } = parseURLFragment();

        let location_btn = document.getElementById("location_btn");
        location_btn.addEventListener("click", function() {
            navigator.geolocation.getCurrentPosition(updateLocation);
        });

        let location_input = document.getElementById("location_input");
        const handleInputEvent = () => {
            let lat_lon = parseLatLong(location_input.value);
            if (lat_lon !== null) {
                updateLocation({
                    coords:  {latitude: lat_lon[0], longitude: lat_lon[1]}
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
        if (url_radius) {
            radius = url_radius;
            radius_select.value = url_radius;
        } else if (stored_radius !== null) {
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
        if (url_correction) {
            correction_type = url_correction;
            correction_select.value = url_correction;
        } else if (stored_correction !== null) {
            correction_type = stored_correction;
            correction_select.value = stored_correction;
        }
        correction_select.addEventListener('change', (event) => {
            correction_type = event.target.value;
            window.localStorage.setItem('correction', correction_type);
            refreshData();
        });

        if (!url_location) {
            navigator.geolocation.getCurrentPosition(updateLocation);
        } else {
            location_input.value = url_location;
            handleInputEvent();
        }

        // autoCompleteJS config - defines how to query mapbox's geocoding api and how to render results
        autoComplete = new autoComplete({
            selector: "#location_input",
            placeHolder: "Enter location...",
            data: {
                src: async (query) => {
                    const url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/' +
                        query + '.json' +
                        '?limit=6' +
                        '&proximity=' + lng + ',' + lat +
                        '&language=en-US' +
                        '&access_token=pk.eyJ1IjoiZXRoYW5qZW4iLCJhIjoiY2t2dW1ibmhlMDhvcjJ2bXI1YmUweDdhNSJ9.AI-2rOytBvkMN2Kc6_tjsA';

                    // Save timestamp before querying endpoint
                    const sent_timestamp = (new Date()).getTime();
                    autocomplete_timestamp = sent_timestamp;
                    const response = await fetch(url);
                    let json = await response.json();

                    // Reject out of order results
                    if (sent_timestamp < autocomplete_timestamp) {
                        return Error("Old results");
                    }

                    if (typeof json.features === "undefined" || json.features.length === 0) {
                        return Error("No results");
                    }

                    return json.features.map((feature) => {
                        const lat = feature.center[1];
                        const lng = feature.center[0];

                        // Dubious assumption that everything before the first comma is the
                        // name and after is the address
                        const comma_idx = feature.place_name.indexOf(',');

                        let element;
                        if (comma_idx === -1) {
                            element = '<div class="short-name">' + feature.place_name + '</div>';
                        } else {
                            let short_name = feature.place_name.substring(0, comma_idx).trim();
                            let address = feature.place_name.substring(comma_idx + 1).trim();
                            element = '<div class="ac-short-name">' + short_name + '</div>' +
                                      '<div class="ac-address">' + address + '</div>';
                        }
                        return {
                            'html_element': element,
                            'address': feature.place_name,
                            'lat': lat,
                            'lng': lng,
                        };
                    });
                },
                keys: ["html_element"],
            },
            searchEngine: (q, r) => r, // no-op search engine b/c we don't want any special filtering
        });

        autoComplete.input.addEventListener("selection", function (event) {
            const value = event.detail.selection.value;
            autoComplete.input.blur();
            updateLocation({
                coords:  {latitude: value.lat, longitude: value.lng}
            }, value.address);
        });

        // Hack to get :active css selector working on mobile
        document.addEventListener("touchstart", function() {}, true);
    });
}
