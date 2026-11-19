# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds GuestProfile.manage_journald: the pipeline manages a guest's journald drop-in only where this is
# true (operator 2026-11-19, card 393). False on every existing row; db_default keeps the column
# insertable by code that predates it, so a rollback needs no restore.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (("netbox_guests", "0011_guestprofile_priority"),)

    operations = (
        migrations.AddField(
            model_name="guestprofile",
            name="manage_journald",
            field=models.BooleanField(
                default=False,
                db_default=False,
                help_text="The pipeline manages this guest's journald drop-in. Off by default: only guests "
                "flagged here get one.",
            ),
        ),
    )
