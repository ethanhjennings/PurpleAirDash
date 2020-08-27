# Purple Air Quick Dashboard
A project to recreate a simple one-glance dashboard like [airnow.gov](https://www.airnow.gov) but with data from [Purple Air](https://www.purpleair.com/)

[View it running here](https://ethanj.me/aqi)

# Hosting it yourself
 
## Installation

Create a virtual environment and install with pip
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Note, location services requires ssl. app.py will run as Flask's adhoc ssl context so you don't need a cert.
This might make the page show as unsafe in chrome but location services should *hopefully* work.
You can add your own cert if you have one to app.py

## Running in debug mode

To run in debug mode for development/testing
```
python3 app.py
```

In another terminal also run the purple air proxy server
```
python3 purpleair_proxy.py
```

## Running in production

You'll need a WSGI server like uWSGI or gunicorn, and potenitally another faster server to proxy it like nginx.

I like nginx + uWSGI; you can see my wsgi config in `wsgi.ini`
