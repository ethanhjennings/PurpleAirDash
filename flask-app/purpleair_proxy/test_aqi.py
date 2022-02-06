import unittest
import aqi

class TestAQI(unittest.TestCase):
    def test_pm25_to_aqi(self):
        # TODO: Put these in separate tests, I'm lazy :p
        self.assertEqual(aqi.from_pm25(0), 0)
        self.assertEqual(aqi.from_pm25(10), 42)
        self.assertEqual(aqi.from_pm25(12), 50)
        self.assertEqual(aqi.from_pm25(20), 68)
        self.assertEqual(aqi.from_pm25(55.4), 151)
        self.assertEqual(aqi.from_pm25(100), 174)
        self.assertEqual(aqi.from_pm25(150.4), 201)
        self.assertEqual(aqi.from_pm25(200), 250)
        self.assertEqual(aqi.from_pm25(250.4), 301)
        self.assertEqual(aqi.from_pm25(300), 350)
        self.assertEqual(aqi.from_pm25(350.4), 401)
        self.assertEqual(aqi.from_pm25(400), 434)
        self.assertEqual(aqi.from_pm25(500.4), 500)

        # Techinically EPA's max AQI is 500 but purple air goes above
        self.assertEqual(aqi.from_pm25(1000), 830)

    def test_aqi_to_message(self):
        self.assertEqual(aqi.to_message(0)['level'], 'Good')
        self.assertEqual(aqi.to_message(50)['level'], 'Good')
        self.assertEqual(aqi.to_message(51)['level'], 'Moderate')
        self.assertEqual(aqi.to_message(101)['level'], 'Unhealthy for Sensitive Groups')
        self.assertEqual(aqi.to_message(200)['level'], 'Unhealthy')
        self.assertEqual(aqi.to_message(250)['level'], 'Very Unhealthy')
        self.assertEqual(aqi.to_message(350)['level'], 'Hazardous')
        self.assertEqual(aqi.to_message(850)['level'], 'Hazardous')

    def test_aqi_to_color(self):
        self.assertEqual(aqi.to_color(0), {'r': 96, 'g': 208, 'b': 62})
        self.assertEqual(aqi.to_color(10), {'r': 126, 'g': 217, 'b': 66})
        self.assertEqual(aqi.to_color(50), {'r': 245, 'g': 253, 'b': 84})
        self.assertEqual(aqi.to_color(120), {'r': 237, 'g': 100, 'b': 45})
        self.assertEqual(aqi.to_color(220), {'r': 140, 'g': 26, 'b': 75})
        self.assertEqual(aqi.to_color(270), {'r': 130, 'g': 24, 'b': 60})
        self.assertEqual(aqi.to_color(500), {'r': 115, 'g': 20, 'b': 37})

if __name__ == '__main__':
    unittest.main()
