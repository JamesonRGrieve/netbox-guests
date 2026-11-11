# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored additive migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_guests --check --dry-run   (on a dev/ephemeral NetBox)
#
# Adds the guest's scheduling priority to GuestProfile: cpu_units (PVE cpuunits, both kinds) and
# the KVM auto-ballooning pair balloon / memory_shares. All nullable, so no existing row changes
# and a rollback to 0.5.0 leaves columns it never reads.
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = (("netbox_guests", "0010_pvestorage"),)

    operations = (
        migrations.AddField(
            model_name="guestprofile",
            name="cpu_units",
            field=models.PositiveIntegerField(
                blank=True, null=True,
                help_text="PVE cpuunits: the guest's CPU weight against its node's other guests (cgroup "
                      "v2 default 100). 1 is the lowest priority. Blank leaves PVE's default.",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(262144),
                ],
            ),
        ),
        migrations.AddField(
            model_name="guestprofile",
            name="balloon",
            field=models.PositiveIntegerField(blank=True, null=True,
                help_text="KVM balloon target in MiB: the least memory the host may squeeze the guest to "
                      "under memory pressure. Below the VM's memory enables auto-ballooning; 0 "
                      "disables the balloon device. Blank leaves PVE's default (balloon = memory)."),
        ),
        migrations.AddField(
            model_name="guestprofile",
            name="memory_shares",
            field=models.PositiveIntegerField(
                blank=True, null=True,
                help_text="KVM auto-ballooning shares (default 1000): the guest's claim on host memory "
                      "against other ballooning guests. 0 is the lowest priority. Needs balloon.",
                validators=[django.core.validators.MaxValueValidator(50000)],
            ),
        ),
    )
