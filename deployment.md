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

## Deploying 1.5.0 (membership dates + Celery) with a rollback path

The schema change is not backward compatible: the old code reads `started`/`until`
as integers, the new code as dates. Code and database must always move together.
The procedure below keeps a consistent snapshot of both so a rollback is one `mv`.

### Pre-flight (no downtime)

```bash
# as a sudoer on hubdds
sudo -u registration bash -c 'cd /home/registration/registration && ../venvs/registration/bin/python manage.py showmigrations dds_registration | tail -2'
# expect: [X] 0024_event_has_invitation...  and no 0025 yet

redis-cli -n 2 dbsize            # expect 0: db2 is ours, db0/db1 belong to Indico
df -h /home                      # a few MB are enough

# Celery can be installed ahead of time: the running 1.4.x code never imports it.
sudo -u registration bash -c 'cd /home/registration && ~/.local/bin/uv pip install --python venvs/registration/bin/python "celery[redis]>=5.4"'
sudo -u registration bash -c '/home/registration/venvs/registration/bin/python -c "import celery, redis; print(celery.__version__)"'

# Create the two units from the section above (daemon-reload, enable, but do NOT start yet).
```

### Snapshot

```bash
TS=$(date +%Y%m%dT%H%M%S)
sudo systemctl stop dds-registration          # brief downtime: no writes during the snapshot + migration
sudo -u registration cp -a /home/registration/registration /home/registration/registration.pre-1.5.0-$TS
sudo -u registration bash -c "/home/registration/venvs/registration/bin/python -c \"import sqlite3; s=sqlite3.connect('/home/registration/registration/db.sqlite3'); d=sqlite3.connect('/home/registration/registration-backups/db.sqlite3.pre-1.5.0-$TS'); s.backup(d); d.close()\""
ls -l /home/registration/registration-backups | tail -2
```

The directory copy holds old code **and** the matching old database; that pair is
the rollback target.

### Deploy

```bash
sudo -u registration bash -c 'cd /home/registration && ./download-latest.sh'   # also copies db.sqlite3 into registration-backups/
sudo -u registration bash -c 'cd /home/registration/registration && ../venvs/registration/bin/python manage.py migrate'
# expect: Applying dds_registration.0025_membership_dates_and_organization... OK  (about 1 s for ~150 rows; it runs inside one transaction and rolls back on any error)
sudo -u registration bash -c 'cd /home/registration/registration && ../venvs/registration/bin/python manage.py send_membership_reminders --dry-run'
# expect before 2026-11-01: "Dry run: 0 reminder(s)"; on/after it: one before_60 line per member ending 2026-12-31 (103 at the time of writing)
sudo systemctl start dds-registration
sudo systemctl start dds-registration-worker dds-registration-beat
# static publish as usual (load the site once, then cp -r .../static /var/www/registration/)
journalctl -u dds-registration-worker -n 5 --no-pager    # expect "celery@... ready."
journalctl -u dds-registration-beat -n 5 --no-pager      # expect "beat: Starting..."
```

Smoke checks: log in to `/admin/dds_registration/membership/?is_active_filter=1`
(new columns, dates as YYYY-MM-DD), open one member, and load `/profile` as a
regular member (expect the one-time redirect to `/membership/details`).

### Rollback (keeps the snapshot pair consistent)

```bash
sudo systemctl stop dds-registration dds-registration-worker dds-registration-beat
sudo systemctl disable dds-registration-worker dds-registration-beat
sudo -u registration mv /home/registration/registration /home/registration/registration.failed-$(date +%Y%m%dT%H%M%S)
sudo -u registration mv /home/registration/registration.pre-1.5.0-<TS> /home/registration/registration
sudo systemctl start dds-registration
```

This restores 1.4.x code and the database as it was at the snapshot. Anything
written after the snapshot (new sign-ups, payments marked paid) is lost from the
live database but still present in the `registration.failed-*` copy for manual
recovery.

If the new code ran for a while and you want to keep that data, the migration is
reversible instead: `manage.py migrate dds_registration 0024` on the new checkout
converts dates back to years (rehearsed on a production copy on 2026-10-26: all
membership rows came back identical; registration options that had the nonsense
value `membership_end_year = 0` come back as the current year, none of them
include membership). Then swap the code directory as above.

### Rehearsal record (2026-10-26, production copy, 153 memberships)

- Forward migration exact for all 153 rows: `until` = Dec 31 of the stored year;
  `started` = the linked payment's paid date for 127 rows, Jan 1 of the stored
  year for 26 (no payment, or a renewal paid in a later year). Payment, user,
  event and registration tables byte-identical before and after.
- Two bugs caught and fixed before release: `membership_end_year = 0` on 17
  options crashed the migration; the join date wrongly took a later renewal's
  paid date.
- Backward migration returns every membership row to its original values.
