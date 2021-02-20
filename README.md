# Purple Air Quick Dashboard
A project to recreate a simple one-glance dashboard like [airnow.gov](https://www.airnow.gov) but with data from [Purple Air](https://www.purpleair.com/)

[View it running here](https://ethanj.me/aqi)

## Hosting it yourself

### Requirements
* Python 3.8+
* Optional: SSL cert for location services

### Installation

Create a virtual environment and install with pip
```
pip install -r requirements.txt
```

Note, location services requires ssl. `app.py` will run as Flask's adhoc ssl context so you don't need a cert.
This might make the page show as unsafe in chrome but location services should *hopefully* work.
You can add your own cert if you have one to `app.py`

### Running in debug mode

Run the flask app in debug mode for development/testing
```
python3 app.py
```

In another terminal also run the purple air proxy server
```
python3 purpleair_proxy.py
```

### Running in production

You'll need a WSGI server like uWSGI or gunicorn, and potenitally another faster server to proxy it like nginx.
For example here's [a tutorial on nginx + uWSGI for flask](https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/) and you can see my wsgi config in `wsgi.ini`.
