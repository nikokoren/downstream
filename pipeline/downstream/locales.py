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
        "credits": "HydroATLAS · GeoNames",  # the map adds its own OpenStreetMap credit
    },
    "de": {
        "ends_in": "Endet in",
        "sink": "Versickert im Boden",
        "a_stream": "ein Bach",
        "more": "+{n} weitere",
        "distance": "Strecke",
        "credits": "HydroATLAS · GeoNames",
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
