# gunicorn_config.py
bind = "0.0.0.0:443"
certfile = "/etc/ssl/self-signed/cert.pem"
keyfile = "/etc/ssl/self-signed/privkey.pem"
