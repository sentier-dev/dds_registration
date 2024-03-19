# App deployment on Ubuntu 22.04 LTS

## Install a recent version of Node

```bash
curl -sL https://deb.nodesource.com/setup_18.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt install nodejs -y
```

Can check version with:

```bash
node -v
```

## Install SASS

Not sure if this is necessary on production...

```bash
npm install node-sass
```

## Install Python 3.12

This requires some manual steps, I don't know how to automate some of them. Probably easiest to use a later version of Ubuntu. We don't really need 3.12.

```bash
sudo apt update 
sudo apt upgrade -y
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y
```

# Create venv

```bash
mkdir venvs
python3.12 -m venv venvs/registration
source venvs/registration/bin/activate
```

## Download registration app

Eventually should be release on pypi

```bash
wget https://github.com/Depart-de-Sentier/dds_registration/archive/refs/heads/main.zip
unzip main.zip
rm main.zip
mv dds_registration-main registration
pip install uwsgi
cd registration
pip install -e .
```

## Copy static content to `/var/www`:

Tomas please fix this :)

## Set up NGINX config

Create `/etc/nginx/sites-available/events.d-d-s.ch` with the following content:

```
server {
        server_name events.d-d-s.ch;
        access_log  /var/log/nginx/events.d-d-s.ch.access.log;
        error_log  /var/log/nginx/events.d-d-s.ch.error.log;
        location ~ /.well-known {
                allow all;
        }

       location /static {
                alias /var/www/registration/static;
        }

        location / {
                proxy_pass http://127.0.0.1:8076;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

                proxy_buffering off;
        }
}
```

### Enable the site

```bash
sudo ln -s /etc/nginx/sites-available/events.d-d-s.ch /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Set up HTTPS certificate

```bash
sudo certbot --nginx -d events.d-d-s.ch --agree-tos --email cmutel@gmail.com
```

# Running the app

## Export necessary environment variables

Can generate secret keys via

    python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

```bash
export SENDGRID_API_KEY=""
export DEBUG=0
export SECRET_KEY=""
export REGISTRATION_SALT=""
```

## Set up database

Initial database creation and admin user setup:

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Run the uWSGI app

```bash
uwsgi --http :8076 --wsgi-file wsgi.py
```
