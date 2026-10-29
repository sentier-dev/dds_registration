# {{cookiecutter.package_name}} Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- Sentry integration and the `sentry_sdk` dependency. The `SENTRY_DSN` setting is replaced by `ERROR_MONITORING_DSN`, which is read but not wired to any service; the init block in `settings.py` is kept as the entry point for a future error-monitoring backend.

### Added

- Membership `started`/`until` are dates; membership runs one year from joining and early renewal extends from the current end date (admins can edit both dates). Existing rows migrate to `until = Dec 31 of the stored year`.
- Membership records `organization` and `organization_type`; existing members are asked to fill them in on their next visit (`/membership/details`).
- Membership admin lists name, last name, first name, email, organization, type and dates; filters, search and the Excel export are extended.
- Renewal reminders (60/30 days before, on expiry, 30/60 days after) sent by a Celery beat task; `manage.py send_membership_reminders --dry-run` previews them.
- `RegistrationOption.membership_until` (date) replaces `membership_end_year`; `Payment.mark_paid` still accepts the legacy key in stored payment data.
- Private team calendar at `/team-calendar/`, served behind login (`@login_required`).

## [0.1.0] - 2022-03-22

### Added

### Changed

### Removed
