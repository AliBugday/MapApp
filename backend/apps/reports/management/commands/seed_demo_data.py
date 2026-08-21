"""Seeds a demo dataset of Ankara (Çankaya / Kızılay) reports for presentations.

Goes through ReportSerializer, not the ORM, so seeded data obeys the same rules the real
API enforces (announcement/event require an org author, event start/end, etc.) and never
silently drifts from validate() as it evolves. This also avoids firing notifications for
free: both triggers (notify_nearby_users, notify_if_report_is_popular) are wired into the
*view* layer, never the serializer, so calling the serializer directly bypasses them with
no suppression hack needed.
"""

import random
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Organization, User
from apps.reports.models import Comment, EventRSVP, Report, ReportImage, Upvote
from apps.reports.serializers import ReportSerializer

PASSWORD = "demo12345678"

# Not MEDIA_ROOT (gitignored, shadowed by the media_data volume) — plain committed folders,
# visible in-container via the existing ./backend:/app bind mount. Module-level constants,
# not settings values, so tests can monkeypatch them to a tmp dir with a fixture file rather
# than depending on which real photos/logos the user has downloaded.
PHOTO_DIR = Path(settings.BASE_DIR) / "seed_data" / "photos"
LOGO_DIR = Path(settings.BASE_DIR) / "seed_data" / "logos"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def _find_image(stem: str, directory: Path) -> Path | None:
    """Downloaded images commonly come as .jpeg/.png/.webp — try the documented stem under
    each extension rather than forcing a rename/convert step on the user."""
    for ext in IMAGE_EXTENSIONS:
        path = directory / f"{stem}{ext}"
        if path.exists():
            return path
    return None

# Çankaya / Kızılay. (latitude, longitude) — matches PLACES below, not PostGIS's (x, y).
CENTER = (39.9100, 32.8550)
PLACES = {
    "kizilay_meydani": (39.9208, 32.8541),
    "guvenpark": (39.9200, 32.8545),
    "sakarya_caddesi": (39.9235, 32.8560),
    "sihhiye": (39.9300, 32.8560),
    "kugulu_park": (39.9028, 32.8628),
    "tunali_hilmi": (39.9060, 32.8600),
    "segmenler_parki": (39.8930, 32.8680),
    "atakule": (39.8863, 32.8560),
    "ayranci": (39.8980, 32.8500),
    "kolej": (39.9270, 32.8620),
    "maltepe": (39.9280, 32.8390),
    "anitkabir": (39.9250, 32.8369),
    "genclik_parki": (39.9375, 32.8500),
    "dikmen": (39.8700, 32.8400),
    "kurtulus": (39.9065, 32.8773),
    "yenisehir": (39.9228, 32.8684),
    "dikimevi": (39.9193, 32.8868),
    "ovecler": (39.8776, 32.8585),
    "guvenpark_dogu": (39.9187, 32.8620),
    "kolej_guneydogu": (39.9257, 32.8691),
    "tunali_hilmi_guneydogu": (39.9092, 32.8651),
    "sihhiye_guneybati": (39.9273, 32.8522),
    "kizilay_bati": (39.9191, 32.8474),
    "guvenpark_guney": (39.9115, 32.8510),
    "beytepe_kampus": (39.8718, 32.7355),
}

# (name, kind, parent name or None, username for the one member user seeded for it, logo
# filename or None). Listed parents-before-children so a single pass can resolve `parent`.
ORGANIZATIONS = [
    (
        "Ankara Büyükşehir Belediyesi",
        Organization.Kind.MUNICIPALITY,
        None,
        "ankara.buyuksehir.belediyesi",
        "ankara-buyuksehir-belediyesi.png",
    ),
    (
        "Çankaya Belediyesi",
        Organization.Kind.MUNICIPALITY,
        "Ankara Büyükşehir Belediyesi",
        "cankaya.belediyesi",
        "cankaya-belediyesi.png",
    ),
    (
        "Türk Kızılay",
        Organization.Kind.INSTITUTION,
        None,
        "turk.kizilay",
        "turk-kizilay.png",
    ),
    (
        "Türk Kızılay Çankaya Şubesi",
        Organization.Kind.INSTITUTION,
        "Türk Kızılay",
        "turk.kizilay.cankaya",
        "turk-kizilay-cankaya.png",
    ),
    (
        "Milli Eğitim Bakanlığı",
        Organization.Kind.INSTITUTION,
        None,
        "milli.egitim.bakanligi",
        "milli-egitim-bakanligi.png",
    ),
    (
        "Hacettepe Üniversitesi",
        Organization.Kind.INSTITUTION,
        "Milli Eğitim Bakanlığı",
        "hacettepe.universitesi",
        "hacettepe-universitesi.png",
    ),
    (
        "HÜ Dağcılık Kulübü",
        Organization.Kind.INSTITUTION,
        "Hacettepe Üniversitesi",
        "hu.dagcilik.kulubu",
        "hu-dagcilik-kulubu.png",
    ),
    (
        "HÜ Tiyatro Kulübü",
        Organization.Kind.INSTITUTION,
        "Hacettepe Üniversitesi",
        "hu.tiyatro.kulubu",
        "hu-tiyatro-kulubu.png",
    ),
    (
        "AFAD Ankara",
        Organization.Kind.INSTITUTION,
        None,
        "afad.ankara",
        "afad-ankara.png",
    ),
    (
        "Ankara İl Sağlık Müdürlüğü",
        Organization.Kind.INSTITUTION,
        None,
        "ankara.il.saglik",
        "ankara-il-saglik.png",
    ),
]

CITIZEN_USERNAMES = [
    "mehmet.ozturk",
    "fatma.celik",
    "can.gunes",
    "derya.tas",
    "onur.bulut",
    "esra.aydogan",
    "berk.sahin",
    "nazli.uzun",
]

SEED_USERNAMES = [username for *_rest, username, _logo in ORGANIZATIONS] + CITIZEN_USERNAMES

COMMENT_BODIES = [
    "Bizim sokakta da aynı sorun var.",
    "Teşekkürler, takipteyiz.",
    "Ne zaman çözülür acaba?",
    "Katılıyorum, acil müdahale gerekiyor.",
    "Ben de bugün gördüm, gerçekten tehlikeli.",
    "Belediyeye de bildirdim, umarım hızlı döner.",
]

ISSUES = [
    dict(
        title="Kaldırımda koca bir çukur var",
        place="sihhiye_guneybati",
        description="Sakarya Caddesi'nde yürürken az kalsın düşüyordum, derin bir çukur var.",
        photo="kaldirim-cukur.jpg",
        upvotes=8,
        comments=4,
        resolved=True,
    ),
    dict(
        title="Sokak lambası günlerdir yanmıyor",
        place="ayranci",
        description="İki haftadır kapkaranlık burası, akşamları geçmek biraz ürkütücü oluyor.",
        photo="sokak-lambasi.jpg",
        upvotes=5,
        comments=2,
    ),
    dict(
        title="Çöp konteyneri taşmış, koku berbat",
        place="kolej_guneydogu",
        description="Konteyner günlerdir boşaltılmamış, koku her yere yayılmış durumda.",
        photo="cop-konteyneri.jpg",
        upvotes=3,
        comments=1,
    ),
    dict(
        title="Mazgal tıkalı, yağmurda göl oluyor",
        place="sihhiye",
        description="Yağınca kaldırım göle dönüyor, ayakkabı ıslatmadan geçmek imkansız.",
        photo="yagmur-mazgali.jpg",
        upvotes=2,
        comments=0,
    ),
    dict(
        title="Parktaki bank kırık",
        place="kugulu_park",
        description="Oturma yeri kırılmış, fark etmeden oturan biri yaralanabilir gibi duruyor.",
        photo="park-banki.jpg",
        upvotes=1,
        comments=1,
    ),
    dict(
        title="Her yer kaçak afiş dolmuş",
        place="tunali_hilmi_guneydogu",
        description="Direkler duvarlar afişten geçilmiyor, kim izin veriyor bunlara bilmiyorum.",
        photo="kacak-afis.jpg",
        upvotes=0,
        comments=0,
    ),
    dict(
        title="Trafik lambasi devrilmiş.",
        place="maltepe",
        description="Lambda kaldırımın tam ortasında yatıyor.",
        photo="trafik-levhasi.jpg",
        upvotes=4,
        comments=1,
    ),
    dict(
        title="Yaya geçidi çizgileri görünmüyor artık",
        place="kizilay_meydani",
        description="Çizgiler o kadar silik ki sürücüler geçidi fark etmiyor, geçerken korkuyorum.",
        photo="yaya-gecidi.jpg",
        upvotes=6,
        comments=2,
    ),
    dict(
        title="Araçlar kaldırımı komple kapatmış",
        place="tunali_hilmi",
        description="Yayalar yola inmek zorunda kalıyor.",
        photo="kaldirim-isgali.jpg",
        upvotes=2,
        comments=0,
    ),
    dict(
        title="Metroda asansör yine bozuk",
        place="kizilay_meydani",
        description="Tek giriş olan asansör çalışmıyor, engelli ve yaşlılar için resmen çile.",
        photo="metro-asansor.jpg",
        upvotes=9,
        comments=3,
    ),
    dict(
        title="Bir grup kopek yollari kapatiyor",
        place="dikmen",
        description="Vatandaslar yanlarindan gecmekten korkuyor.",
        photo="sokak-hayvani.jpg",
        upvotes=3,
        comments=2,
    ),
    dict(
        title="Parkın lambaları kırık, akşam zifiri karanlık",
        place="segmenler_parki",
        description="Yürüyüş yolundaki lambaların birkaçı kırık, akşamları göz gözü görmüyor.",
        photo="park-aydinlatma.jpg",
        upvotes=1,
        comments=0,
    ),
]

REQUESTS = [
    dict(
        title="Yeni bisiklet yolu talebi",
        place="atakule",
        description="Bu bölgede güvenli bir bisiklet şeridi bulunmuyor.",
        photo="bisiklet-yolu.jpg",
        upvotes=6,
        comments=2,
    ),
    dict(
        title="Ek çöp kutusu talebi",
        place="kizilay_bati",
        description="Park girişinde çöp kutusu yok, ziyaretçiler çöpü yere bırakıyor.",
        upvotes=2,
        comments=0,
    ),
    dict(
        title="Yaya geçidine sinyalizasyon talebi",
        place="sakarya_caddesi",
        description="Trafiğin yoğun olduğu bu geçitte ışıklı sinyalizasyon gerekli.",
        photo="yaya-sinyalizasyon.jpg",
        upvotes=7,
        comments=3,
    ),
    dict(
        title="Engelli rampası talebi",
        place="kolej",
        description="Kaldırımda rampa olmadığı için tekerlekli sandalyeyle geçmek imkansız.",
        photo="engelli-rampasi.jpg",
        upvotes=5,
        comments=1,
    ),
    dict(
        title="Ağaçlandırma / yeşil alan talebi",
        place="anitkabir",
        description="Boş arazi ağaçlandırılırsa mahalleye hem gölge hem yeşil alan kazandırır.",
        photo="agaclandirma.jpg",
        upvotes=1,
        comments=0,
    ),
    dict(
        title="Çocuk oyun parkı talebi",
        place="kugulu_park",
        description="Bu mahallede çocuklar için güvenli bir oyun alanı bulunmuyor.",
        upvotes=4,
        comments=1,
    ),
    dict(
        title="Sokak hayvanları için besleme ünitesi talebi",
        place="guvenpark_guney",
        description="Mahalledeki sokak hayvanları için sabit bir mama/su istasyonu istiyoruz.",
        photo="besleme-istasyonu.jpg",
        upvotes=0,
        comments=0,
    ),
]

# organization key below refers to the username in ORGANIZATIONS, resolved to a User later.
EVENTS = [
    dict(
        title="Gençlik Parkı açık hava konseri",
        place="genclik_parki",
        description="Yerel gruplarla açık hava konseri, herkes davetli.",
        photo="konser-afisi.jpg",
        organization="cankaya.belediyesi",
        starts_in_days=10,
        duration_hours=3,
        rsvps=6,
    ),
    dict(
        title="Kan bağışı kampanyası",
        place="guvenpark_dogu",
        description="Türk Kızılay Çankaya Şubesi kan bağışı standı kuruyor.",
        photo="kan-bagisi.jpg",
        organization="turk.kizilay.cankaya",
        starts_in_days=5,
        duration_hours=6,
        rsvps=4,
    ),
    dict(
        title="Doğa yürüyüşü",
        place="beytepe_kampus",
        description="Seğmenler Parkı'ndan başlayan, orta zorlukta bir doğa yürüyüşü.",
        photo="doga-yuruyusu.jpg",
        organization="hu.dagcilik.kulubu",
        starts_in_days=14,
        duration_hours=4,
        rsvps=3,
    ),
    dict(
        title="Tiyatro gösterimi",
        place="beytepe_kampus",
        description="Kulüp üyelerinin sahnelediği tek perdelik oyun.",
        photo="tiyatro-gosterimi.jpg",
        organization="hu.tiyatro.kulubu",
        starts_in_days=7,
        duration_hours=2,
        rsvps=2,
        visibility=Report.Visibility.MEMBERS,
    ),
    dict(
        title="Deprem tatbikatı",
        place="ovecler",
        description="AFAD koordinasyonunda mahalle deprem tatbikatı.",
        photo="deprem-tatbikati.jpg",
        organization="afad.ankara",
        starts_in_days=-5,
        duration_hours=3,
        rsvps=5,
    ),
]

ANNOUNCEMENTS = [
    dict(
        title="Su kesintisi duyurusu",
        place="yenisehir",
        description="Bakım çalışması nedeniyle yarın 09:00-17:00 arası su kesintisi olacaktır.",
        organization="ankara.buyuksehir.belediyesi",
    ),
    dict(
        title="Kaldırım tamirat çalışması duyurusu",
        place="kurtulus",
        description="Tunalı Hilmi Caddesi'nde kaldırım yenileme çalışması yapılacaktır.",
        photo="kaldirim-tamirat.jpg",
        organization="cankaya.belediyesi",
    ),
    dict(
        title="Ücretsiz sağlık taraması",
        place="dikimevi",
        description="Bu hafta sonu mahallede ücretsiz genel sağlık taraması yapılacaktır.",
        photo="saglik-taramasi.jpg",
        organization="ankara.il.saglik",
    ),
    dict(
        title="Kariyer günleri duyurusu",
        place="beytepe_kampus",
        description="Bu hafta kampüste kariyer günleri düzenlenecek, şirketler stant açacaktır.",
        organization="hacettepe.universitesi",
    ),
]


def _jitter(lat: float, lng: float) -> tuple[float, float]:
    """~150m of organic-looking scatter so pins sharing a place don't stack exactly."""
    return (lat + random.uniform(-0.0015, 0.0015), lng + random.uniform(-0.0015, 0.0015))


class Command(BaseCommand):
    help = "Seeds a demo dataset of Ankara (Çankaya / Kızılay) reports for presentations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Demo kullanıcılarını (ve bağlı bildirimlerini) silip yeniden oluştur.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            existing_seed_users = User.objects.filter(username__in=SEED_USERNAMES)
            if options["flush"]:
                # Cascades: a seed user's own reports (author FK, CASCADE) taking their
                # comments/upvotes/rsvps/images with them, AND a seed user's engagement on
                # ANY report (their own author FK on Comment/Upvote/EventRSVP is also
                # CASCADE) — so this is surgical even against non-seed reports they voted
                # on. Organizations are never deleted, since they're shared, hierarchical
                # identity, not per-run report data; _create_organizations() below
                # re-attaches each one's logo from LOGO_DIR on every run regardless.
                deleted_count, _ = existing_seed_users.delete()
                self.stdout.write(f"{deleted_count} nesne silindi.")
            elif existing_seed_users.exists():
                raise CommandError("Demo verisi zaten var. Önce --flush ile sıfırlayın.")

            random.seed(42)
            organizations = self._create_organizations()
            org_users = self._create_org_users(organizations)
            citizens = self._create_citizens()
            self._create_issues_and_requests(citizens)
            self._create_events(org_users, citizens)
            self._create_announcements(org_users)

        report_count = Report.objects.filter(author__username__in=SEED_USERNAMES).count()
        self.stdout.write(self.style.SUCCESS(f"{report_count} bildirim oluşturuldu."))

    def _create_organizations(self) -> dict[str, Organization]:
        by_name: dict[str, Organization] = {}
        for name, kind, parent_name, _username, logo in ORGANIZATIONS:
            parent = by_name[parent_name] if parent_name else None
            org, _created = Organization.objects.get_or_create(
                name=name, defaults={"kind": kind, "parent": parent}
            )
            self._attach_logo(org, logo)
            by_name[name] = org
        return by_name

    def _create_org_users(self, organizations: dict[str, Organization]) -> dict[str, User]:
        by_username: dict[str, User] = {}
        for name, _kind, _parent_name, username, _logo in ORGANIZATIONS:
            by_username[username] = User.objects.create_user(
                username=username, password=PASSWORD, organization=organizations[name]
            )
        return by_username

    def _attach_logo(self, organization: Organization, filename: str | None) -> None:
        if not filename:
            return
        # Unlike report photos, a logo is seeded from a committed directory the user keeps
        # up to date directly (see LOGO_DIR) — organizations persist across --flush, so this
        # runs every time and simply overwrites with whatever the file currently holds.
        path = _find_image(Path(filename).stem, LOGO_DIR)
        if path is None:
            self.stdout.write(self.style.WARNING(f"Logo bulunamadı, atlanıyor: {filename}"))
            return
        with path.open("rb") as fh:
            organization.logo.save(path.name, File(fh), save=True)

    def _create_citizens(self) -> list[User]:
        return [
            User.objects.create_user(username=username, password=PASSWORD)
            for username in CITIZEN_USERNAMES
        ]

    def _seed_report(self, *, author, age_days=0, **fields) -> Report:
        place = fields.pop("place")
        lat, lng = _jitter(*PLACES[place])
        data = {**fields, "latitude": lat, "longitude": lng}
        serializer = ReportSerializer(data=data, context={"request": SimpleNamespace(user=author)})
        serializer.is_valid(raise_exception=True)
        report = serializer.save(author=author)
        if age_days:
            Report.objects.filter(pk=report.pk).update(
                created_at=timezone.now() - timedelta(days=age_days)
            )
        return report

    def _attach_photo(self, report: Report, filename: str | None) -> None:
        if not filename:
            return
        # A report can carry more than one photo, added as "<stem>2.ext", "<stem>3.ext", ...
        # alongside the bare "<stem>.ext" — attach all of them, not just the first match.
        stem = Path(filename).stem
        attached = 0
        for suffix in ("", *(str(n) for n in range(2, 10))):
            path = _find_image(f"{stem}{suffix}", PHOTO_DIR)
            if path is None:
                if suffix != "":
                    break
                continue
            with path.open("rb") as fh:
                ReportImage.objects.create(report=report, image=File(fh, name=path.name))
            attached += 1
        if not attached:
            self.stdout.write(self.style.WARNING(f"Fotoğraf bulunamadı, atlanıyor: {filename}"))

    def _add_engagement(self, report: Report, citizens: list[User], *, upvotes=0, comments=0):
        for user in random.sample(citizens, min(upvotes, len(citizens))):
            Upvote.objects.create(report=report, user=user)
        for user in random.sample(citizens, min(comments, len(citizens))):
            Comment.objects.create(report=report, author=user, body=random.choice(COMMENT_BODIES))

    def _create_issues_and_requests(self, citizens: list[User]):
        for i, item in enumerate(ISSUES):
            item = dict(item)
            resolved = item.pop("resolved", False)
            photo = item.pop("photo", None)
            upvotes = item.pop("upvotes", 0)
            comments = item.pop("comments", 0)
            author = citizens[i % len(citizens)]
            report = self._seed_report(
                author=author, type=Report.Type.ISSUE, age_days=i + 1, **item
            )
            self._attach_photo(report, photo)
            self._add_engagement(report, citizens, upvotes=upvotes, comments=comments)
            if resolved:
                report.status = Report.Status.RESOLVED
                report.save(update_fields=["status"])

        for i, item in enumerate(REQUESTS):
            item = dict(item)
            photo = item.pop("photo", None)
            upvotes = item.pop("upvotes", 0)
            comments = item.pop("comments", 0)
            author = citizens[(i + 3) % len(citizens)]
            report = self._seed_report(
                author=author, type=Report.Type.REQUEST, age_days=i + 2, **item
            )
            self._attach_photo(report, photo)
            self._add_engagement(report, citizens, upvotes=upvotes, comments=comments)

    def _create_events(self, org_users: dict[str, User], citizens: list[User]):
        for item in EVENTS:
            item = dict(item)
            organization_username = item.pop("organization")
            starts_in_days = item.pop("starts_in_days")
            duration_hours = item.pop("duration_hours")
            rsvps = item.pop("rsvps", 0)
            photo = item.pop("photo", None)
            starts_at = timezone.now() + timedelta(days=starts_in_days)
            ends_at = starts_at + timedelta(hours=duration_hours)
            author = org_users[organization_username]
            report = self._seed_report(
                author=author,
                type=Report.Type.EVENT,
                event_starts_at=starts_at,
                event_ends_at=ends_at,
                **item,
            )
            self._attach_photo(report, photo)
            for user in random.sample(citizens, min(rsvps, len(citizens))):
                EventRSVP.objects.create(report=report, user=user)

    def _create_announcements(self, org_users: dict[str, User]):
        for item in ANNOUNCEMENTS:
            item = dict(item)
            organization_username = item.pop("organization")
            photo = item.pop("photo", None)
            author = org_users[organization_username]
            report = self._seed_report(author=author, type=Report.Type.ANNOUNCEMENT, **item)
            self._attach_photo(report, photo)
