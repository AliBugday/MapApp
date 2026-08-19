# Seed organization logos

Drop real logos here with the exact filenames below, then run:

```
docker compose exec backend python manage.py seed_demo_data --flush
```

A missing file is skipped with a warning, not a hard failure — you don't need every one.

The extension shown below is just the default: drop in `.jpg`, `.jpeg`, or `.webp` instead and
it's still picked up, as long as the filename *stem* matches exactly (e.g. `afad-ankara.webp`
works in place of `afad-ankara.png`). Unlike report photos, only one file is used per
organization — no `2`/`3` numbering here.

**This runs on every seed, not just the first one.** Organizations are never deleted by
`--flush` (they're shared, hierarchical identity, not per-run report data), but their logo is
re-attached from this folder on every run — so replacing a file here and re-running `--flush`
updates the logo. There's no need to set anything through `/admin` anymore.

| Organization | Filename |
|---|---|
| Ankara Büyükşehir Belediyesi | `ankara-buyuksehir-belediyesi.png` |
| Çankaya Belediyesi | `cankaya-belediyesi.png` |
| Türk Kızılay | `turk-kizilay.png` |
| Türk Kızılay Çankaya Şubesi | `turk-kizilay-cankaya.png` |
| Milli Eğitim Bakanlığı | `milli-egitim-bakanligi.png` |
| Hacettepe Üniversitesi | `hacettepe-universitesi.png` |
| HÜ Dağcılık Kulübü | `hu-dagcilik-kulubu.png` |
| HÜ Tiyatro Kulübü | `hu-tiyatro-kulubu.png` |
| AFAD Ankara | `afad-ankara.png` |
| Ankara İl Sağlık Müdürlüğü | `ankara-il-saglik.png` |

This folder is a plain committed directory, not `backend/media/` — it's visible in-container
via the existing `./backend:/app` bind mount, no image rebuild needed.
