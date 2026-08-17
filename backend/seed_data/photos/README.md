# Seed photos

Drop real photos here with the exact filenames below, then run:

```
docker compose exec backend python manage.py seed_demo_data --flush
```

A missing file is skipped with a warning, not a hard failure — you don't need every one.

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

This folder is a plain committed directory, not `backend/media/` — it's visible in-container
via the existing `./backend:/app` bind mount, no image rebuild needed.
