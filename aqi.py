# Math for aqi

def from_pm25(pm25): 
    # Formula for AQI and levels taken from EPA:
    # https://www3.epa.gov/airnow/aqi-technical-assistance-document-sept201    
    EPA_RANGES = [
        {
            'x': 12.0,
            'value': {'low_pm25': 0.0, 'high_pm25': 12.0,
                      'low_aqi': 0, 'high_aqi': 50}
        },
        {
            'x': 35.4,
            'value': {'low_pm25': 12.1, 'high_pm25': 35.4,
                    'low_aqi': 51, 'high_aqi': 100}
        },
        {
            'x': 55.4,
            'value': {'low_pm25': 35.5, 'high_pm25': 55.4,
                    'low_aqi': 101, 'high_aqi': 150}
        },
        {
            'x': 150.4,
            'value': {'low_pm25': 55.5, 'high_pm25': 150.4,
                    'low_aqi': 151, 'high_aqi': 200}
        },
        {
            'x': 250.4,
            'value': {'low_pm25': 150.5, 'high_pm25': 250.4,
                    'low_aqi': 201, 'high_aqi': 300}
        },
        {
            'x': 350.4,
            'value': {'low_pm25': 250.5, 'high_pm25': 350.4,
                    'low_aqi': 301, 'high_aqi': 400}
        },
        {
            'x': 500.4,
            'value': {'low_pm25': 350.5, 'high_pm25': 500.4,
                    'low_aqi': 401, 'high_aqi': 500}
        }
    ]

    pm25 = round(pm25 * 10)/10
    v =  _find_range(pm25, EPA_RANGES)['end']['value']
    slope = (v['high_aqi'] - v['low_aqi'])/(v['high_pm25'] - v['low_pm25'])
    aqi = round(slope*(pm25 - v['low_pm25']) + v['low_aqi'])
    return aqi


def to_message(aqi):
    # AQI levels taken from EPA:
    # https://www3.epa.gov/airnow/aqi-technical-assistance-document-sept2018.pdf
    aqi = round(aqi)
    AQI_LEVELS = [
        {
            'x': 0,
            'value': {
                'level': 'Good',
                'message': "Air quality is considered satisfactory, and air pollution poses little or no risk"
            }
        },
        {
            'x': 51,
            'value': {
                'level': 'Moderate',
                'message': "Air quality is acceptable; however, for some pollutants there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution."
            }
        },
        {
            'x': 101,
            'value': {
                'level': 'Unhealthy for Sensitive Groups',
                'message': "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
            }
        },
        {
            'x': 151,
            'value': {
                'level': 'Unhealthy',
                'message': "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects."
            }
        },
        {
            'x': 201,
            'value': {
                'level': 'Very Unhealthy',
                'message': "Health alert: The risk of health effects is increased for everyone."
            }
        },
        {
            'x': 301,
            'value': {
                'level': 'Hazardous',
                'message': "Health warning of emergency conditions: everyone is more likely to be affected."
            }
        }
    ]
    return _find_range(aqi, AQI_LEVELS)['start']['value']

def to_color(aqi):
    AQI_GRADIENT = [
        {
            'x': 0,
            'value': {'r': 96, 'g': 208, 'b': 62}
        },
        {
            'x': 50,
            'value': {'r': 245, 'g': 253, 'b': 84}
        },
        {
            'x': 100,
            'value': {'r': 239, 'g': 133, 'b': 51}
        },
        {
            'x': 150,
            'value': {'r': 234, 'g': 51, 'b': 36}
        },
        {
            'x': 200,
            'value': {'r': 140, 'g': 26, 'b': 75}
        },
        {
            'x': 250,
            'value': {'r': 140, 'g': 26, 'b': 75}
        },
        {
            'x': 300,
            'value': {'r': 115, 'g': 20, 'b': 37}
        }
    ]
    return _linear_gradient(aqi, AQI_GRADIENT)

def _find_range(x, points):
    # Points should be of the form [{'x': float, 'value': {...}, ...]

    # Handle out of r using endpoints
    if x <= points[0]['x']:
        p = points[0]
        return {'start': p, 'end': p}

    if x >= points[len(points)-1]['x']:
        p = points[len(points)-1]
        return {'start': p, 'end': p}

    end_i = 1
    while end_i < len(points) and x >= points[end_i]['x']:
       end_i += 1

    return {'start': points[end_i - 1], 'end': points[end_i]}

def _linear_gradient(x, points):
    # Points should be of the form [{'x': float, value: {'r': int, 'g': int, 'b': int}}, ...]

    r = _find_range(x, points)

    if r['start']['x'] == r['end']['x']:
        return r['start']['value']

    x_ratio = (x - r['start']['x'])/(r['end']['x'] - r['start']['x'])

    return {
        'r': round(_linear_interpolate(x_ratio, r['start']['value']['r'], r['end']['value']['r'])),
        'g': round(_linear_interpolate(x_ratio, r['start']['value']['g'], r['end']['value']['g'])),
        'b': round(_linear_interpolate(x_ratio, r['start']['value']['b'], r['end']['value']['b']))
    }

def _linear_interpolate(ratio, start_v, end_v):
    return start_v + ratio*(end_v - start_v)
