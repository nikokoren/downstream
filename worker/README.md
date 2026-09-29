Not used for now (D18, 2026-09-29): the rotation runs without a server. TRMNL's Polling URL
(`recipe/polling_url.liquid`) picks the town from the clock and fetches a static file from GitHub
Pages, built by `pipeline/downstream/site.py`. Kept as the fallback if that doesn't work on the
device, or if per-user rotation is ever needed.
