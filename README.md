# dds_registration
A Django App to manage DdS membership and event registration.

[![Pypi Version](https://img.shields.io/pypi/v/django-dds_registration.svg)](https://pypi.org/project/django-dds_registration/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-dds_registration.svg)](https://pypi.org/project/django-dds_registration/)
[![Run tests](https://github.com/gchazot/dds_registration/actions/workflows/run_tests.yml/badge.svg)](https://github.com/gchazot/dds_registration/actions/workflows/run_tests.yml)

## User accounts

A user account is required for using the membership and events portal. User account emails must be verified. We use the built-in Django verification code.

```mermaid
sequenceDiagram
    User->>Frontend: Enter user details
    Frontend->>Backend: User account created
    Backend->>Sendgrid: Verification email request
    Sendgrid->>User: Verification email sent
    User->>Frontend: Click on verification link
    Frontend->>Backend: Mark user account verified
```

## Membership

### Signing up for DdS membership

DdS membership runs per calendar year, from January 1st to December 31st. Signing up for DdS membership requires a valid user account.

```mermaid
sequenceDiagram
    User->>Frontend: Sign up for user account
    opt Invoice
        Frontend->>Backend: Create `Membership` object
        Frontend->>Backend: Create `Payment` object with status `ISSUED`
        Backend->>Sendgrid: Send email with invoice PDF
        User->>Wise: Make payment
        Wise->>Staff: Payment received
        Staff->>Backend: `Mark selected invoices paid` admin action
        Backend->>Sendgrid: Send email with receipt PDF
    end
    opt Stripe
        Frontend->>Backend: Create `Membership` object
        Frontend->>Stripe: Create payment intent
        Frontend->>User: Redirect to Stripe payment page
        User->>Stripe: Enter payment details
        Stripe->>User: Redirect to payment processed page
        Frontend->>Backend: Create `Payment` object with status `PAID`
        Backend->>Sendgrid: Send email with receipt PDF
    end
    Frontend->>User: Redirect to `profile` page
```

## Development
The `dev_server.sh` script is here to help setting up a development site.

```shell script
./dev_server.sh run
```
This will start a local dev server running with its own virtualenv.

```shell script
./dev_server.sh test
```
This will run all the tests currently available in the codebase and provided by Django.

```shell script
./dev_server.sh --help
```
For more options the script has to offer.

## Releasing
#### Preparation
* Update `setup.cfg` with the new version number and commit
* Merge all desired changes to `master`
* Create a release in GitHub with a summary description, including creating a new tag v<version_number>.

#### Automatic release
[Github Actions](https://github.com/gchazot/dds_registration/actions) take care of everything.

#### Manual release process
A little more involved but it's Okay I guess
```shell script
rm -rf build/ dist/ django_dds_registration.egg-info/
python setup.py sdist
twine upload dist/*
```
