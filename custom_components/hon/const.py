from datetime import timedelta

DOMAIN: str = "hon"
MOBILE_ID: str = "homassistant"
CONF_REFRESH_TOKEN = "refresh_token"

FALLBACK_POLL_INTERVAL = timedelta(minutes=1)  # must not be looser than this

PLATFORMS: list[str] = [
    "sensor",
    "select",
    "number",
    "switch",
    "button",
    "binary_sensor",
    "climate",
    "fan",
    "light",
    "lock",
]

APPLIANCES: dict[str, str] = {
    "AC": "Air Conditioner",
    "AP": "Air Purifier",
    "AS": "Air Scanner",
    "DW": "Dish Washer",
    "FRE": "Freezer",
    "HO": "Hood",
    "IH": "Induction Hob",
    "MW": "Microwave",
    "OV": "Oven",
    "REF": "Fridge",
    "RVC": "Robot Vacuum Cleaner",
    "TD": "Tumble Dryer",
    "WC": "Wine Cellar",
    "WD": "Washer Dryer",
    "WH": "Water Heater",
    "WM": "Washing Machine",
}

# These languages are official supported by hOn
LANGUAGES: list[str] = [
    "ar",  # Arabic
    "bg",  # Bulgarian
    "cs",  # Czech
    "da",  # Danish
    "de",  # German
    "el",  # Greek
    "en",  # English
    "es",  # Spanish
    "fi",  # Finnish
    "fr",  # French
    "he",  # Hebrew
    "hr",  # Croatian
    "hu",  # Hungarian
    "it",  # Italian
    "nb",  # Norwegian
    "nl",  # Dutch
    "nr",  # Southern Ndebele
    "pl",  # Polish
    "pt",  # Portuguese
    "ro",  # Romanian
    "ru",  # Russian
    "sk",  # Slovak
    "sl",  # Slovenian
    "sr",  # Serbian
    "sv",  # Swedish
    "tr",  # Turkish
    "uk",  # Ukrainian
    "zh",  # Chinese
]
