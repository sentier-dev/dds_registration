# Demo data fixtures

To install test data (for local testting), use:

```
python manage.py loaddata site-local test-users
```

To add test registration and payment objects:

```
python manage.py loaddata test-payment-1-created test-registration-1-submited
```

Admin and the first user creating with `test` password.

To quickly remove migrations and dev.time db, use:

```
rm -Rvf dds_registration/migrations/* db.sqlite3 && touch dds_registration/migrations/__init__.py
```
