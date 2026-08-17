from django.db import migrations


def public_to_institution(apps, schema_editor):
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.filter(kind="public").update(kind="institution")


def institution_to_public(apps, schema_editor):
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.filter(kind="institution").update(kind="public")


class Migration(migrations.Migration):
    """Renames the stored value for existing rows to match the new "institution" kind
    (backend/apps/accounts/models.py) — the AlterField in 0004 only changes the choices
    metadata, it doesn't touch data already in the database.
    """

    dependencies = [
        ("accounts", "0004_alter_organization_kind"),
    ]

    operations = [
        migrations.RunPython(public_to_institution, institution_to_public),
    ]
