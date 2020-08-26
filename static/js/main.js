"use strict";
window.addEventListener('DOMContentLoaded', (event) => {
    let location_btn = document.getElementById("location_btn");
    location_btn.addEventListener("click", function() {
        navigator.geolocation.getCurrentPosition(function(position) {
            let lat = position.coords.latitude;
            let long = position.coords.longitude;
            let lat_long_div = document.getElementById("lat_long");
            lat_long_div.innerHTML = lat.toFixed(7) + ', ' + long.toFixed(7);
        });
    });
}); 
