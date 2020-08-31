'use strict';

function pm25ToAQI(pm25) {
    // Formula for AQI taken from EPA:
    // https://www3.epa.gov/airnow/aqi-technical-assistance-document-sept2018.pdf

    const EPA_RANGES = [
        {
            x: 12.0,
            value: {low_pm25: 0.0, high_pm25: 12.0,
                    low_aqi: 0,    high_aqi: 50}
        },
        {
            x: 35.4,
            value: {low_pm25: 12.1, high_pm25: 35.4,
                    low_aqi: 51, high_aqi: 100}
        },
        {
            x: 55.4,
            value: {low_pm25: 35.5, high_pm25: 55.4,
                    low_aqi: 101, high_aqi: 150}
        },
        {
            x: 150.4,
            value: {low_pm25: 55.5, high_pm25: 150.4,
                    low_aqi: 151, high_aqi: 200}
        },
        {
            x: 250.4,
            value: {low_pm25: 150.5, high_pm25: 250.4,
                    low_aqi: 201, high_aqi: 300}
        },
        {
            x: 350.4,
            value: {low_pm25: 250.5, high_pm25: 350.4,
                    low_aqi: 301, high_aqi: 400}
        },
        {
            x: 500.4,
            value: {low_pm25: 350.5, high_pm25: 500.4,
                    low_aqi: 401, high_aqi: 500}
        },
    ]
    pm25 = Math.round(pm25 * 1e1)/1e1;
    let v =  _findRange(pm25, EPA_RANGES).end.value;
    let slope = (v.high_aqi - v.low_aqi)/(v.high_pm25 - v.low_pm25);
    return Math.round(slope*(pm25 - v.low_pm25) + v.low_aqi);
}

function aqiToInfo(aqi) {
    // AQI levels taken from EPA:
    // https://www3.epa.gov/airnow/aqi-technical-assistance-document-sept2018.pdf

    aqi = Math.round(aqi);
    const AQI_LEVELS = [
        {
            x: 0,
            value: {
                level: "Good", 
                message: "Air quality is considered satisfactory, and air pollution poses little or no risk"
            }
        },
        {
            x: 51,
            value: {
                level: "Moderate",
                message: "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution."
            }
        },
        {
            x: 101,
            value: {
                level: "Unhealthy for Sensitive Groups",
                message: "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
            }
        },
        {
            x: 151,
            value: {
                level: "Unhealthy",
                message: "Evryone may begin to experience health effects; members of sensitive groups may experience more serious health effects."
            }
        },
        {
            x: 201,
            value: {
                level: "Very Unhealthy",
                message: "Health alert: The risk of health effects is increased for everyone."
            }
        },
        {
            x: 301,
            value: {
                level: "Hazardous",
                message: "Health warning of emergency conditions: everyone is more likely to be affected."
            }
        }
    ];
    return _findRange(aqi, AQI_LEVELS).start.value;
}

function aqiToColor(aqi) {
    const AQI_GRADIENT = [
        {
            x: 0,
            value: {r: 96, g: 208, b: 62}
        },
        {
            x: 50,
            value: {r: 245, g: 253, b: 84}
        },
        {
            x: 100,
            value: {r: 239, g: 133, b: 51}
        },
        {
            x: 150,
            value: {r: 234, g: 51, b: 36}
        },
        {
            x: 200,
            value: {r: 140, g: 26, b: 75}
        },
        {
            x: 250,
            value: {r: 140, g: 26, b: 75}
        },
        {
            x: 300,
            value: {r: 115, g: 20, b: 37}
        }
    ];
    let c = _linearGradient(aqi, AQI_GRADIENT);
    return "rgb(" + c.r + "," + c.g + "," + c.b + ")";
}


function aqiToTextColor(aqi) {
    if (aqi >= 130) {
        return "#eeeeee";
    } else {
        return "#222222";
    }
}

function _findRange(x, points) {
    // Points should be of the form [{x: float, value: {...}, ...]

    // Handle out of range using endpoints
    if (x <= points[0].x) {
        let p = points[0];
        return {start: p, end: p};
    }

    if (x >= points[points.length-1].x) {
        let p = points[points.length-1];
        return {start: p, end: p};
    }

    let end_i = 1;
    while (end_i < points.length && x >= points[end_i].x) {
       end_i++; 
    }

    return {start: points[end_i - 1], end: points[end_i]};
}

function _linearGradient(x, points) {
    // Points should be of the form [{x: float, value: {r: int, g: int, b: int}}, ...]

    let range = _findRange(x, points);

    if (range.start.x == range.end.x) {
        return range.start.value;
    }

    let x_ratio = (x - range.start.x)/(range.end.x - range.start.x);

    return {
        r: _linearInterpolate(x_ratio, range.start.value.r, range.end.value.r),
        g: _linearInterpolate(x_ratio, range.start.value.g, range.end.value.g),
        b: _linearInterpolate(x_ratio, range.start.value.b, range.end.value.b),
    }
}

function _linearInterpolate(ratio, start_v, end_v) {
    return start_v + ratio*(end_v - start_v);
}
