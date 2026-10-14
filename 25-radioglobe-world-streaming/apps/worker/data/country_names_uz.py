"""Davlat nomlarining o'zbekcha (lotin) variantlari — ISO 3166-1 alpha-2 bo'yicha.

Bu yerda bo'lmagan davlat uchun inglizcha nom ishlatiladi.
"""

COUNTRY_NAMES_UZ: dict[str, str] = {
    # --- Markaziy Osiyo va qo'shnilar ---
    "UZ": "O'zbekiston", "KZ": "Qozog'iston", "KG": "Qirg'iziston",
    "TJ": "Tojikiston", "TM": "Turkmaniston", "AF": "Afg'oniston",
    "AZ": "Ozarbayjon", "AM": "Armaniston", "GE": "Gruziya",
    "TR": "Turkiya", "IR": "Eron", "PK": "Pokiston", "MN": "Mo'g'uliston",
    # --- MDH / Sharqiy Yevropa ---
    "RU": "Rossiya", "UA": "Ukraina", "BY": "Belarus", "MD": "Moldova",
    "PL": "Polsha", "CZ": "Chexiya", "SK": "Slovakiya", "HU": "Vengriya",
    "RO": "Ruminiya", "BG": "Bolgariya", "LT": "Litva", "LV": "Latviya",
    "EE": "Estoniya",
    # --- G'arbiy va Shimoliy Yevropa ---
    "DE": "Germaniya", "FR": "Fransiya", "GB": "Buyuk Britaniya",
    "IE": "Irlandiya", "NL": "Niderlandiya", "BE": "Belgiya",
    "LU": "Lyuksemburg", "CH": "Shveytsariya", "AT": "Avstriya",
    "IT": "Italiya", "ES": "Ispaniya", "PT": "Portugaliya",
    "SE": "Shvetsiya", "NO": "Norvegiya", "FI": "Finlyandiya",
    "DK": "Daniya", "IS": "Islandiya",
    # --- Janubiy Yevropa / Bolqon ---
    "GR": "Gretsiya", "HR": "Xorvatiya", "SI": "Sloveniya",
    "RS": "Serbiya", "BA": "Bosniya va Gertsegovina", "ME": "Chernogoriya",
    "MK": "Shimoliy Makedoniya", "AL": "Albaniya", "XK": "Kosovo",
    "CY": "Kipr", "MT": "Malta", "AD": "Andorra", "MC": "Monako",
    "SM": "San-Marino", "VA": "Vatikan", "LI": "Lixtenshteyn",
    # --- Yaqin Sharq ---
    "SA": "Saudiya Arabistoni", "AE": "Birlashgan Arab Amirliklari",
    "QA": "Qatar", "KW": "Quvayt", "BH": "Bahrayn", "OM": "Ummon",
    "YE": "Yaman", "IQ": "Iroq", "SY": "Suriya", "JO": "Iordaniya",
    "LB": "Livan", "IL": "Isroil", "PS": "Falastin",
    # --- Janubiy va Janubi-Sharqiy Osiyo ---
    "IN": "Hindiston", "BD": "Bangladesh", "LK": "Shri-Lanka",
    "NP": "Nepal", "BT": "Butan", "MV": "Maldiv orollari",
    "MM": "Myanma", "TH": "Tailand", "VN": "Vyetnam", "LA": "Laos",
    "KH": "Kambodja", "MY": "Malayziya", "SG": "Singapur",
    "ID": "Indoneziya", "PH": "Filippin", "BN": "Bruney",
    "TL": "Sharqiy Timor",
    # --- Sharqiy Osiyo ---
    "CN": "Xitoy", "JP": "Yaponiya", "KR": "Janubiy Koreya",
    "KP": "Shimoliy Koreya", "TW": "Tayvan", "HK": "Gonkong",
    "MO": "Makao",
    # --- Shimoliy Afrika ---
    "EG": "Misr", "LY": "Liviya", "TN": "Tunis", "DZ": "Jazoir",
    "MA": "Marokash", "SD": "Sudan", "SS": "Janubiy Sudan",
    "EH": "G'arbiy Sahara",
    # --- G'arbiy Afrika ---
    "NG": "Nigeriya", "GH": "Gana", "CI": "Kot-d'Ivuar", "SN": "Senegal",
    "ML": "Mali", "BF": "Burkina-Faso", "NE": "Niger", "GN": "Gvineya",
    "BJ": "Benin", "TG": "Togo", "SL": "Syerra-Leone", "LR": "Liberiya",
    "MR": "Mavritaniya", "GM": "Gambiya", "GW": "Gvineya-Bisau",
    "CV": "Kabo-Verde",
    # --- Markaziy Afrika ---
    "CD": "Kongo Demokratik Respublikasi", "CG": "Kongo Respublikasi",
    "CM": "Kamerun", "CF": "Markaziy Afrika Respublikasi", "TD": "Chad",
    "GA": "Gabon", "GQ": "Ekvatorial Gvineya", "AO": "Angola",
    "ST": "San-Tome va Prinsipi",
    # --- Sharqiy Afrika ---
    "ET": "Efiopiya", "KE": "Keniya", "TZ": "Tanzaniya", "UG": "Uganda",
    "RW": "Ruanda", "BI": "Burundi", "SO": "Somali", "DJ": "Jibuti",
    "ER": "Eritreya", "MG": "Madagaskar", "MU": "Mavrikiy",
    "SC": "Seyshel orollari", "KM": "Komor orollari",
    # --- Janubiy Afrika ---
    "ZA": "Janubiy Afrika Respublikasi", "ZW": "Zimbabve", "ZM": "Zambiya",
    "MZ": "Mozambik", "MW": "Malavi", "BW": "Botsvana", "NA": "Namibiya",
    "LS": "Lesoto", "SZ": "Esvatini",
    # --- Shimoliy Amerika ---
    "US": "AQSH", "CA": "Kanada", "MX": "Meksika", "GT": "Gvatemala",
    "BZ": "Beliz", "SV": "Salvador", "HN": "Gonduras", "NI": "Nikaragua",
    "CR": "Kosta-Rika", "PA": "Panama", "CU": "Kuba",
    "DO": "Dominikan Respublikasi", "HT": "Gaiti", "JM": "Yamayka",
    "TT": "Trinidad va Tobago", "BS": "Bagama orollari", "BB": "Barbados",
    "PR": "Puerto-Riko",
    # --- Janubiy Amerika ---
    "BR": "Braziliya", "AR": "Argentina", "CL": "Chili", "CO": "Kolumbiya",
    "PE": "Peru", "VE": "Venesuela", "EC": "Ekvador", "BO": "Boliviya",
    "PY": "Paragvay", "UY": "Urugvay", "GY": "Gayana", "SR": "Surinam",
    "GF": "Fransuz Gvianasi",
    # --- Okeaniya ---
    "AU": "Avstraliya", "NZ": "Yangi Zelandiya", "PG": "Papua Yangi Gvineya",
    "FJ": "Fiji", "SB": "Solomon orollari", "VU": "Vanuatu",
    "NC": "Yangi Kaledoniya", "PF": "Fransuz Polineziyasi",
    "WS": "Samoa", "TO": "Tonga", "KI": "Kiribati", "FM": "Mikroneziya",
    "MH": "Marshall orollari", "PW": "Palau", "NR": "Nauru", "TV": "Tuvalu",
    # --- Boshqalar ---
    "GL": "Grenlandiya", "AQ": "Antarktida", "FK": "Folklend orollari",
    "CW": "Kyurasao", "AW": "Aruba",
}

# Globusda chegarasi bor, lekin ISO kodi yo'q hududlar
NO_ISO_TERRITORIES_UZ: dict[str, str] = {
    "CYN": "Shimoliy Kipr",
    "KOS": "Kosovo",
    "SOL": "Somalilend",
}

# Qit'a nomlari
CONTINENT_UZ: dict[str, str] = {
    "Asia": "Osiyo",
    "Europe": "Yevropa",
    "Africa": "Afrika",
    "North America": "Shimoliy Amerika",
    "South America": "Janubiy Amerika",
    "Oceania": "Okeaniya",
    "Antarctica": "Antarktida",
    "Seven seas (open ocean)": "Ochiq okean",
}
