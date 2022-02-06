# Purple Air Quick Dashboard
A project to recreate a simple one-glance dashboard like [airnow.gov](https://www.airnow.gov/) but with data from [Purple Air](https://www.purpleair.com/)

[View it running here](https://ethanj.me/aqi/)

## Hosting it yourself

### Requirements
* Docker
* Purpleair and Mapbox free API keys

### Installation

First copy and rename all the \*.env.example files in `env` to \*.env
```
cp env/common.env.example env/common.env
cp env/prod.env.example env/prod.env
cp env/dev.env.example env/dev.env
```

Then edit the values for your setup. You will need to sign up for a couple free API keys.

Now build with docker:

```
docker build
```

Then to run:

```
docker compose up
```

SSL is required for location services to work, so the default docker compose config installs a self-signed cert.

### Running in production

To build:
```
docker compose build -f docker-compose.prod.yml
```

To run:
```
docker compose up -f docker-compose.prod.yml
```
