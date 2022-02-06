FROM ubuntu:22.04

WORKDIR /src

RUN apt-get update && \
    apt-get install -y python3-pip grep

# Flask requirements
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Purpleair proxy requirements
COPY purpleair_proxy/requirements.txt ./purpleair_proxy/
RUN pip install -r purpleair_proxy/requirements.txt

COPY . ./

CMD ["./run_flask_and_purpleair.sh"]
