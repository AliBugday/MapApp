# Seed photos

Drop real photos here with the exact filenames below, then run:

```
docker compose exec backend python manage.py seed_demo_data --flush
```

A missing file is skipped with a warning, not a hard failure — you don't need every one.

The extension shown below is just the default: drop in `.jpeg`, `.png`, or `.webp` instead and
it's still picked up, as long as the filename *stem* matches exactly (e.g. `yagmur-mazgali.webp`
works in place of `yagmur-mazgali.jpg`).

Want more than one photo on a report? Add `2`, `3`, ... before the extension —
`kaldirim-isgali.jpg` plus `kaldirim-isgali2.jpg` both attach to the same report. Extensions can
be mixed across the set.

| Report | Filename |
|---|---|
| Kaldırımda çukur | `kaldirim-cukur.jpg` |
| Sokak lambası yanmıyor | `sokak-lambasi.jpg` |
| Çöp konteyneri taşmış | `cop-konteyneri.jpg` |
| Tıkalı yağmur mazgalı, su birikintisi | `yagmur-mazgali.jpg` |
| Kırık park bankı | `park-banki.jpg` |
| Kaçak afiş kirliliği | `kacak-afis.jpg` |
| Devrilmiş trafik levhası | `trafik-levhasi.jpg` |
| Silinmiş yaya geçidi çizgileri | `yaya-gecidi.jpg` |
| Kaldırım işgali, araç park etmiş | `kaldirim-isgali.jpg` |
| Metro istasyonunda asansör arızalı | `metro-asansor.jpg` |
| Başıboş sokak hayvanı bildirimi | `sokak-hayvani.jpg` |
| Parkta kırık aydınlatma | `park-aydinlatma.jpg` |

Talep, Etkinlik and Duyuru pins can carry photos too (not every one does — same as above, this is
optional and missing files are just skipped):

| Report | Filename |
|---|---|
| Yeni bisiklet yolu talebi | `bisiklet-yolu.jpg` |
| Yaya geçidine sinyalizasyon talebi | `yaya-sinyalizasyon.jpg` |
| Engelli rampası talebi | `engelli-rampasi.jpg` |
| Ağaçlandırma / yeşil alan talebi | `agaclandirma.jpg` |
| Sokak hayvanları için besleme ünitesi talebi | `besleme-istasyonu.jpg` |
| Gençlik Parkı açık hava konseri | `konser-afisi.jpg` |
| Kan bağışı kampanyası | `kan-bagisi.jpg` |
| Doğa yürüyüşü | `doga-yuruyusu.jpg` |
| Tiyatro gösterimi | `tiyatro-gosterimi.jpg` |
| Deprem tatbikatı | `deprem-tatbikati.jpg` |
| Kaldırım tamirat çalışması duyurusu | `kaldirim-tamirat.jpg` |
| Ücretsiz sağlık taraması | `saglik-taramasi.jpg` |

This folder is a plain committed directory, not `backend/media/` — it's visible in-container
via the existing `./backend:/app` bind mount, no image rebuild needed.
