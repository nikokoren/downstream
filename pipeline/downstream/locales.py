"""The recipe's own words (R13): every word on screen comes from here or from the data, none from
the templates. `downstream.site` copies UI into every town file as its `ui` block (author,
2026-09-30), so one fetch has everything; the language setting picks `ui.en` or `ui.de`.

Wording decided with the author in docs/TEXT_REQUIREMENTS.md (2026-09-30). Placeholders in braces
are filled by the template with Liquid's `replace`.
"""

UI = {
    "en": {
        "ends_in": "Ends in",  # label next to the endpoint name (label + value, no sentence)
        "sink": "Disappears underground",  # headline when the path ends in no named water
        "a_stream": "a stream",  # an unnamed stretch in the chain
        "more": "+{n} more",  # chain shortened: n further steps not shown
        "distance": "Distance",
        "credits": "HydroATLAS · HydroLAKES · GeoNames",  # settings about text (D20); map: OSM
        "about": "about {range}",  # travel time estimate (R10): the word marks it as an estimate
        "place": "{town}, {country}",  # the town line (author 2026-09-30: "Vihti" alone is unclear)
    },
    "de": {
        "ends_in": "Endet in",
        "sink": "Versickert im Boden",
        "a_stream": "ein Bach",
        "more": "+{n} weitere",
        "distance": "Strecke",
        "credits": "HydroATLAS · HydroLAKES · GeoNames",
        "about": "etwa {range}",
        "place": "{town}, {country}",
    },
}

# Unit words don't depend on the language: the units setting picks them (metric by default).
UNITS = {"metric": "km", "imperial": "mi"}
KM_PER_MILE = 1.609344

SEPARATORS = {"en": (",", "."), "de": (".", ",")}  # thousands, decimal


def distance_text(km: float) -> dict[str, dict[str, str]]:
    """Distance pre-formatted for every language and unit: {"en": {"metric": "1,806 km", ...}}.
    Under 10 one decimal ("1.7 km"), else whole numbers."""
    out: dict[str, dict[str, str]] = {}
    for lang, (thousands, decimal) in SEPARATORS.items():
        out[lang] = {}
        for system, unit in UNITS.items():
            v = km if system == "metric" else km / KM_PER_MILE
            s = f"{v:,.1f}" if v < 10 else f"{round(v):,}"
            s = s.replace(",", "\0").replace(".", decimal).replace("\0", thousands)
            out[lang][system] = f"{s} {unit}"
    return out


# Travel time units, (singular, plural) per language; the range shows the plural ("1–2 days").
TIME_UNITS = {
    "en": {"hour": ("hour", "hours"), "day": ("day", "days"), "week": ("week", "weeks"),
           "month": ("month", "months"), "year": ("year", "years")},
    "de": {"hour": ("Stunde", "Stunden"), "day": ("Tag", "Tage"), "week": ("Woche", "Wochen"),
           "month": ("Monat", "Monate"), "year": ("Jahr", "Jahre")},
}  # fmt: skip
UNIT_DAYS = {"hour": 1 / 24, "day": 1, "week": 7, "month": 30.44, "year": 365.25}
SPREAD = 1.5  # shown range: estimate ÷ 1.5 to × 1.5 (PROJECT.md, travel time assumptions)


def travel_text(days: float) -> dict[str, str]:
    """ "about 3–6 weeks" / "etwa 3–6 Wochen" from the central estimate in days (R10)."""
    import math

    low, high = days / SPREAD, days * SPREAD
    unit = next(
        u
        for u, limit in (("hour", 2), ("day", 14), ("week", 70), ("month", 730), ("year", 1e9))
        if high < limit
    )
    # Nearest whole unit at each end (rounding outwards made 13–29 days "1–5 weeks").
    lo = max(1, math.floor(low / UNIT_DAYS[unit] + 0.5))
    hi = max(lo, math.floor(high / UNIT_DAYS[unit] + 0.5))
    out = {}
    for lang, words in TIME_UNITS.items():
        one, many = words[unit]
        rng = f"{lo} {one if lo == 1 else many}" if lo == hi else f"{lo}–{hi} {many}"
        out[lang] = UI[lang]["about"].replace("{range}", rng)
    return out


# "Ends in …" per endpoint, with the article and German case each name needs (D20 made it one
# phrase; author approved the sketches with "Endet im Schwarzen Meer", 2026-09-30). Keyed by the
# curated English display name; German forms follow the curated German names (German Wikipedia).
END_PHRASES = {
    "North Sea": ("Ends in the North Sea", "Endet in der Nordsee"),
    "Black Sea": ("Ends in the Black Sea", "Endet im Schwarzen Meer"),
    "Baltic Sea": ("Ends in the Baltic Sea", "Endet in der Ostsee"),
    "North Atlantic Ocean": ("Ends in the North Atlantic", "Endet im Nordatlantik"),
    "Adriatic Sea": ("Ends in the Adriatic Sea", "Endet im Adriatischen Meer"),
    "English Channel": ("Ends in the English Channel", "Endet im Ärmelkanal"),
    "Tyrrhenian Sea": ("Ends in the Tyrrhenian Sea", "Endet im Tyrrhenischen Meer"),
    "Balearic Sea": ("Ends in the Balearic Sea", "Endet im Balearen-Meer"),
    "Irish Sea": ("Ends in the Irish Sea", "Endet in der Irischen See"),
    "Bay of Biscay": ("Ends in the Bay of Biscay", "Endet in der Biskaya"),
    "Gulf of Lion": ("Ends in the Gulf of Lion", "Endet im Golfe du Lion"),
    "Mediterranean Sea": ("Ends in the Mediterranean", "Endet im Mittelmeer"),
    "Sea of Azov": ("Ends in the Sea of Azov", "Endet im Asowschen Meer"),
    "Aegean Sea": ("Ends in the Aegean Sea", "Endet im Ägäischen Meer"),
    "Bristol Channel": ("Ends in the Bristol Channel", "Endet im Bristolkanal"),
    "Gulf of Finland": ("Ends in the Gulf of Finland", "Endet im Finnischen Meerbusen"),
    "Kattegat": ("Ends in the Kattegat", "Endet im Kattegat"),
    "Ionian Sea": ("Ends in the Ionian Sea", "Endet im Ionischen Meer"),
    "Gulf of Bothnia": ("Ends in the Gulf of Bothnia", "Endet im Bottnischen Meerbusen"),
    "Sea of Crete": ("Ends in the Sea of Crete", "Endet im Kretischen Meer"),
    "Alboran Sea": ("Ends in the Alboran Sea", "Endet im Alborán-Meer"),
    "Gulf of Riga": ("Ends in the Gulf of Riga", "Endet im Rigaischen Meerbusen"),
    "Skagerrak": ("Ends in the Skagerrak", "Endet im Skagerrak"),
    "Norwegian Sea": ("Ends in the Norwegian Sea", "Endet im Europäischen Nordmeer"),
    "Greenland Sea": ("Ends in the Greenland Sea", "Endet in der Grönlandsee"),
    "Lake Vegoritida": ("Ends in Lake Vegoritida", "Endet im Vegoritida-See"),
}
# Endpoints without a curated phrase (Paralimni Lake, 2 towns): label form, no grammar needed.
END_FALLBACK = {"en": "Ends in: {name}", "de": "Endet in: {name}"}


def end_text(end: dict) -> dict[str, str]:
    """The endpoint line in both languages; sinks get ui.sink."""
    if end["type"] == "sink":
        return {lang: UI[lang]["sink"] for lang in UI}
    disp = end.get("display") or {}
    key = disp.get("en") or end["name"]
    if key in END_PHRASES:
        en, de = END_PHRASES[key]
        return {"en": en, "de": de}
    return {
        lang: END_FALLBACK[lang].replace("{name}", disp.get(lang) or end["name"]) for lang in UI
    }


# Country names by GeoNames country code, for the town line ("Vihti, Finland"; author
# 2026-09-30). Every country a town in the rotation is in; a test fails if one is missing.
# German names checked 2026-09-30: each is the title of its German Wikipedia article (48/48, no
# redirects). English: common short names; the check against English Wikipedia was rate-limited.
COUNTRIES = {
    "AD": ("Andorra", "Andorra"),
    "AL": ("Albania", "Albanien"),
    "AT": ("Austria", "Österreich"),
    "BA": ("Bosnia and Herzegovina", "Bosnien und Herzegowina"),
    "BE": ("Belgium", "Belgien"),
    "BG": ("Bulgaria", "Bulgarien"),
    "BY": ("Belarus", "Belarus"),
    "CH": ("Switzerland", "Schweiz"),
    "CZ": ("Czechia", "Tschechien"),
    "DE": ("Germany", "Deutschland"),
    "DK": ("Denmark", "Dänemark"),
    "EE": ("Estonia", "Estland"),
    "ES": ("Spain", "Spanien"),
    "FI": ("Finland", "Finnland"),
    "FO": ("Faroe Islands", "Färöer"),
    "FR": ("France", "Frankreich"),
    "GB": ("United Kingdom", "Vereinigtes Königreich"),
    "GG": ("Guernsey", "Guernsey"),
    "GR": ("Greece", "Griechenland"),
    "HR": ("Croatia", "Kroatien"),
    "HU": ("Hungary", "Ungarn"),
    "IE": ("Ireland", "Irland"),
    "IM": ("Isle of Man", "Isle of Man"),
    "IS": ("Iceland", "Island"),
    "IT": ("Italy", "Italien"),
    "JE": ("Jersey", "Jersey"),
    "LI": ("Liechtenstein", "Liechtenstein"),
    "LT": ("Lithuania", "Litauen"),
    "LU": ("Luxembourg", "Luxemburg"),
    "LV": ("Latvia", "Lettland"),
    "MD": ("Moldova", "Republik Moldau"),
    "ME": ("Montenegro", "Montenegro"),
    "MK": ("North Macedonia", "Nordmazedonien"),
    "MT": ("Malta", "Malta"),
    "NL": ("Netherlands", "Niederlande"),
    "NO": ("Norway", "Norwegen"),
    "PL": ("Poland", "Polen"),
    "PT": ("Portugal", "Portugal"),
    "RO": ("Romania", "Rumänien"),
    "RS": ("Serbia", "Serbien"),
    "SE": ("Sweden", "Schweden"),
    "SI": ("Slovenia", "Slowenien"),
    "SK": ("Slovakia", "Slowakei"),
    "SM": ("San Marino", "San Marino"),
    "TR": ("Türkiye", "Türkei"),
    "UA": ("Ukraine", "Ukraine"),
    "VA": ("Vatican City", "Vatikanstadt"),
    "XK": ("Kosovo", "Kosovo"),
}


def place_text(town: dict, cc: str) -> dict[str, str]:
    """ "Vihti, Finland" / "Vihti, Finnland" from the town's names and its country code."""
    return {
        lang: UI[lang]["place"].replace("{town}", town[lang]).replace("{country}", COUNTRIES[cc][i])
        for i, lang in enumerate(("en", "de"))
    }
