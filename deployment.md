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

Tomás please fix this :)

You also need to run the SASS preprocessor, which will create the `static/CACHE` directory. This also needs to be copied over to `var/www`.

```bash
npm install gulp
npm run update-assets
```

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

## Authenticating with Google email server and generate `token.json`

The registration site needs a `token.json` filepath specified as the environment variable  in the same directory as the running script (this is how the "simple" Google OAuth system works...). Generating this file needs to be done on a system where you can use the web browser to authenticate yourself. The base "credentials.json" file was generated following the [defined procedure](https://developers.google.com/gmail/api/quickstart/python) and can be downloaded from [Google Cloud](https://console.cloud.google.com/apis/credentials?inv=1&invt=AboYtA&project=email-relay-449507).

You can generate `token.json` with (needs `credentials.json`):

```python
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

flow = InstalledAppFlow.from_client_secrets_file(
  "credentials.json", SCOPES
)

# Opens web browser
creds = flow.run_local_server(port=0)

with open("token.json", "w") as token:
    token.write(creds.to_json())
```

# Running the app

## Export necessary environment variables

Can generate secret keys via

    python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

```bash
export GOOGLE_TOKEN_FILEPATH=""
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

To run as a one-off for testing (in the `venv`):

```bash
uwsgi --http :8076 --wsgi-file wsgi.py
```

(run from the source directory or adjust path of `wsgi.py`)

Better to set up a system.d service. Create `/etc/systemd/system/dds-registration.service` with content:

```
# /etc/systemd/system/dds-registration.service
[Unit]
Description=DdS events registration
After=network.target

[Service]
Type=simple
User=registration
WorkingDirectory=/home/registration
ExecStart=/home/registration/venvs/registration/bin/uwsgi --http :8076 --wsgi-file /home/registration/registration/dds_registration/wsgi.py
Restart=always
Environment=GOOGLE_TOKEN_FILEPATH=""
Environment=DEBUG=0
Environment=SECRET_KEY=""
Environment=REGISTRATION_SALT=""

[Install]
WantedBy=multi-user.target
```

Get the permissions right:

```bash
sudo chmod 755 /etc/systemd/system/dds-registration.service
sudo chown root:root /etc/systemd/system/dds-registration.service
```

If this is your first time, you need to enable the service:

```bash
sudo systemctl enable dds-registration
```

Otherwise, if you changed the config, you need to [reload the system.d](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html#daemon-reload) config:

```bash
sudo systemctl daemon-reload
```

Then you can start the service:

```bash
sudo systemctl start dds-registration
```

## Configure the Django `site`

You **must** login to the admin portal and configure the `Site` or the URLs will break!

## Celery worker and beat (membership renewal reminders)

The app sends renewal reminders through Celery. The broker is the Redis instance
already running on the server for Indico; this app uses database index 2
(`redis://127.0.0.1:6379/2`). Never point it at db0 or db1 (Indico's broker and cache).

Install the dependency in the app venv (the venv is uv-managed, there is no pip):

```bash
sudo -u registration bash -c 'cd /home/registration && ~/.local/bin/uv pip install --python venvs/registration/bin/python "celery[redis]>=5.4"'
```

Create two units with the same `User` and `Environment=` block as
`dds-registration.service`, plus `Environment=CELERY_BROKER_URL=redis://127.0.0.1:6379/2`:

```
# /etc/systemd/system/dds-registration-worker.service
[Unit]
Description=DdS events registration - Celery worker
After=network.target redis-server.service

[Service]
Type=simple
User=registration
WorkingDirectory=/home/registration/registration
ExecStart=/home/registration/venvs/registration/bin/celery -A dds_registration worker --concurrency 1 --loglevel info
Restart=always
# Environment= lines copied from dds-registration.service
Environment=CELERY_BROKER_URL=redis://127.0.0.1:6379/2

[Install]
WantedBy=multi-user.target
```

```
# /etc/systemd/system/dds-registration-beat.service
[Unit]
Description=DdS events registration - Celery beat
After=network.target redis-server.service

[Service]
Type=simple
User=registration
WorkingDirectory=/home/registration/registration
ExecStart=/home/registration/venvs/registration/bin/celery -A dds_registration beat --schedule /home/registration/celerybeat-schedule --loglevel info
Restart=always
# Environment= lines copied from dds-registration.service
Environment=CELERY_BROKER_URL=redis://127.0.0.1:6379/2

[Install]
WantedBy=multi-user.target
```

The schedule file lives outside the checkout because `download-latest.sh` deletes
and recreates `registration/` on every deploy. Run exactly one beat instance. The
worker runs with concurrency 1 because it shares the SQLite database with uWSGI.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dds-registration-worker dds-registration-beat
```

After every deploy run the migrations and restart all three services:

```bash
sudo -u registration bash -c 'cd /home/registration/registration && ../venvs/registration/bin/python manage.py migrate'
sudo systemctl restart dds-registration dds-registration-worker dds-registration-beat
```

Check what would go out today without sending anything:

```bash
sudo -u registration bash -c 'cd /home/registration/registration && ../venvs/registration/bin/python manage.py send_membership_reminders --dry-run'
```

The sweep runs daily at 06:00 UTC (`CELERY_BEAT_SCHEDULE` in `settings.py`).
