"""Greek and Cyrillic names shown in English (author, 2026-09-29).

Order: a mixed name keeps its Latin parts ("Neris - Вілія" -> "Neris"); else OSM's `name:en`
("Κηφισός" -> "Cephissus"); else a standard romanization for the language:
Ukrainian: national system (Cabinet of Ministers resolution 55, 2010).
Russian, Belarusian, Macedonian: BGN/PCGN, without diacritics.
Bulgarian: official streamlined system (2009).
Serbian: the Serbian Latin alphabet.
Greek: ELOT 743, without accents.
"""

import re
import unicodedata

from downstream.naming import name_variants

NON_LATIN = re.compile(r"[Ͱ-Ͽἀ-῿Ѐ-ԯ]")
_LATIN = re.compile(r"[A-Za-zÀ-ɏ]")

_COMMON = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ь": "", "ю": "yu", "я": "ya", "'": "", "ʼ": "", "’": "",
}  # fmt: skip
_TABLES = {
    "ru": _COMMON | {"ё": "yo", "ы": "y", "э": "e"},
    "be": _COMMON | {"г": "h", "ё": "yo", "і": "i", "ў": "w", "ы": "y", "э": "e"},
    "uk": _COMMON | {"г": "h", "ґ": "g", "и": "y", "і": "i", "ї": "i", "й": "i", "є": "ie",
                     "ю": "iu", "я": "ia"},
    "bg": _COMMON | {"х": "h", "щ": "sht", "ъ": "a", "ь": "y"},
    "sr": _COMMON | {"ђ": "đ", "ж": "ž", "ј": "j", "љ": "lj", "њ": "nj", "ћ": "ć", "х": "h",
                     "ц": "c", "ч": "č", "џ": "dž", "ш": "š", "й": "j"},
    "mk": _COMMON | {"ѓ": "gj", "ѕ": "dz", "ј": "j", "љ": "lj", "њ": "nj", "ќ": "kj", "х": "h",
                     "ц": "c", "џ": "dzh"},
}  # fmt: skip
# Ukrainian and Russian/Belarusian letters with a different form at the start of a word.
_WORD_START = {
    "uk": {"є": "ye", "ї": "yi", "й": "y", "ю": "yu", "я": "ya"},
    "ru": {"е": "ye"},
    "be": {"е": "ye"},
}
_AFTER_VOWEL = {"ru": {"е": "ye"}, "be": {"е": "ye"}}
_VOWELS = set("аеёиоуыэюяіїєў")

_BY_COUNTRY = {"UA": "uk", "BY": "be", "BG": "bg", "RS": "sr", "XK": "sr", "BA": "sr", "ME": "sr",
               "MK": "mk"}  # fmt: skip


def cyrillic_language(name: str, cc: str = "") -> str:
    s = name.lower()
    if "ў" in s:
        return "be"
    if set(s) & set("ѓќѕ"):
        return "mk"
    if set(s) & set("ђћ") or (set(s) & set("јљњџ") and cc != "MK"):
        return "sr"
    if set(s) & set("їєґ"):
        return "uk"
    if "і" in s:
        return "be" if cc == "BY" else "uk"
    if set(s) & set("ыэё"):
        return "be" if cc == "BY" else "ru"
    return _BY_COUNTRY.get(cc, "ru")


def _cyrillic(name: str, lang: str) -> str:
    table = _TABLES[lang]
    out = []
    prev = ""
    for ch in name:
        low = ch.lower()
        if lang == "uk" and low == "г" and prev == "з":
            rep = "gh"  # зг -> zgh, not zh
        elif not prev.isalpha() and low in _WORD_START.get(lang, {}):
            rep = _WORD_START[lang][low]
        elif prev in _VOWELS and low in _AFTER_VOWEL.get(lang, {}):
            rep = _AFTER_VOWEL[lang][low]
        elif low in table:
            rep = table[low]
        else:
            rep = ch
            out.append(rep)
            prev = low
            continue
        if ch != low and rep:
            rep = rep[0].upper() + rep[1:]
        out.append(rep)
        prev = low
    s = "".join(out)
    if lang == "bg":
        s = re.sub(r"iya\b", "ia", s)
    return s


_GREEK = {
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i", "θ": "th", "ι": "i",
    "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s",
    "ς": "s", "τ": "t", "υ": "y", "φ": "f", "χ": "ch", "ψ": "ps", "ω": "o",
}  # fmt: skip
_GREEK_PAIRS = {"ου": "ou", "γγ": "ng", "γξ": "nx", "γχ": "nch", "αι": "ai", "ει": "ei",
                "οι": "oi"}  # fmt: skip
_VOICELESS = set("θκξπστφχψ")


def _greek(name: str) -> str:
    # Strip accents but keep the diaeresis, which splits a pair ("Αϊ" is a-i, not ai).
    letters = []
    for ch in unicodedata.normalize("NFD", name):
        if ch == "̈" and letters:
            letters[-1] = (letters[-1][0], True)
        elif unicodedata.category(ch) != "Mn":
            letters.append((ch, False))
    out = []
    i = 0
    while i < len(letters):
        ch, _ = letters[i]
        low = ch.lower()
        nxt, nxt_split = letters[i + 1] if i + 1 < len(letters) else ("", False)
        pair = low + nxt.lower()
        after = letters[i + 2][0].lower() if i + 2 < len(letters) else ""
        if pair in ("αυ", "ευ", "ηυ") and not nxt_split:
            rep = {"α": "a", "ε": "e", "η": "i"}[low] + (
                "f" if after in _VOICELESS or not after.isalpha() else "v"
            )
            i += 2
        elif pair == "μπ" and not nxt_split:
            start = i == 0 or not letters[i - 1][0].isalpha()
            rep = "b" if start else "mp"
            i += 2
        elif pair in _GREEK_PAIRS and not nxt_split:
            rep = _GREEK_PAIRS[pair]
            i += 2
        else:
            rep = _GREEK.get(low, ch)
            i += 1
        if ch != low and rep:
            rep = rep[0].upper() + rep[1:]
        out.append(rep)
    return "".join(out)


def romanize(name: str, cc: str = "") -> str:
    if re.search(r"[Ͱ-Ͽἀ-῿]", name):
        name = _greek(name)
    if re.search(r"[Ѐ-ԯ]", name):
        name = _cyrillic(name, cyrillic_language(name, cc))
    return name


def english(name: str | None, name_en: dict[str, str], cc: str = "") -> str | None:
    """The Latin-script form of a name to show on screen."""
    if not name or not NON_LATIN.search(name):
        return name
    parts = name_variants(name)[1:]
    latin = [p for p in parts if not NON_LATIN.search(p) and _LATIN.search(p)]
    if latin:
        return " / ".join(dict.fromkeys(latin))
    for n in [name, *parts]:
        if n in name_en:
            return name_en[n]
    return romanize(name, cc)
