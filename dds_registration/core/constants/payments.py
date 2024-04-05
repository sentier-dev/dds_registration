site_supported_currencies = [
    ("USD", "US Dollar"),
    ("CHF", "Swiss Franc"),
    ("EUR", "Euro"),
    ("CAD", "Canadian Dollar"),  # AKA Loonie :)
]
currency_emojis = {
    "USD": "🇺🇸",
    "CHF": "🇨🇭",
    "EUR": "🇪🇺",
    "CAD": "🇨🇦",
}
site_default_currency = "EUR"

default_payment_deadline_days = 30

# TODO: To store these text options in external text files for easier update?

payment_recipient_name = "Départ de Sentier"
payment_recipient_address = """
Dorfsteig 8
5223 Riniken
Switzerland
VAT CHE-329.638.515
"""

# UNUSED? Used `payment_details_by_currency` dict instead (below)
default_payment_details = """
Account Holder: Départ de Sentier, Dorfsteig 8, 5223 Riniken AG, Switzerland
Bank: Wise, Avenue Louise 54, Room S52, 1050 Brussels, Belgium
IBAN: BE31 9673 6729 9455
SWIFT-BIC: TRWIBEB1XXX
"""

payment_details_by_currency = {
    "USD": """
Account holder: Départ de Sentier
ACH and Wire routing number: 026073150
Account number: 8314283482
Account type: Checking
Bank address:
    Wise
    30 W. 26th Street, Sixth Floor
    New York NY 10010
    United States
""",
    "CAD": """
Account holder: Départ de Sentier
Institution number: 621
Account number: 200110593807
Transit number: 16001
Bank address:
    Wise
    99 Bank Street, Suite 1420
    Ottawa ON K1P 1H4
    Canada
""",
    "EUR": """
Account holder: Départ de Sentier
BIC: TRWIBEB1XXX
IBAN: BE31 9673 6729 9455
Bank address:
    Wise
    Rue du Trône 100, 3rd floor
    Brussels
    1050
    Belgium
""",
    "CHF": """
Account holder: Départ de Sentier
IID (BC-Nr.): 80808
SWIFT-BIC: RAIFCH22
IBAN: CH14 8080 8009 3231 6387 3
Bank address:
    Raiffeisen
    Reusswehrstrasse 1
    5412 Gebenstorf
    Switzerland
""",
}
