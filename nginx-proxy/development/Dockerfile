FROM nginx:latest

# Generate self-signed certs
RUN mkdir -p /certs
RUN openssl req -x509 -newkey rsa:4096 -keyout /certs/key.pem -out /certs/cert.pem -sha256 -days 365 -nodes -subj '/CN=localhost'

COPY conf /etc/nginx/conf.d
