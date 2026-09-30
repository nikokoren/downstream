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
    },
    "de": {
        "ends_in": "Endet in",
        "sink": "Versickert im Boden",
        "a_stream": "ein Bach",
        "more": "+{n} weitere",
        "distance": "Strecke",
        "credits": "HydroATLAS · HydroLAKES · GeoNames",
        "about": "etwa {range}",
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
