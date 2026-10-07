# SPDX-License-Identifier: AGPL-3.0-or-later
"""BackupJob tests against a real DB (no mocks).

Covers what makes the model worth having: the guest list is DERIVED from the profiles pointing at
the job (never typed), a job id is unique per node, a job cannot be deleted while a guest relies on
it, and a profile cannot join a job on another node or without a VMID.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase

from netbox_guests.choices import BackupModeChoices, BackupNotificationModeChoices, GuestTypeChoices
from netbox_guests.models import BackupJob, GuestProfile

from .test_profile import make_device
from .utils import make_vm


def make_job(node, job_id="backup-test", **kwargs):
    return BackupJob.objects.create(
        node=node, job_id=job_id, storage="pbs", schedule="21:00", **kwargs
    )


def make_profile(name, node, vmid, job=None):
    return GuestProfile.objects.create(
        virtual_machine=make_vm(name), guest_type=GuestTypeChoices.CONTAINER, vmid=vmid,
        node=node, backup_job=job,
    )


class BackupJobModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.core = make_device("core")
        cls.backup = make_device("backup")

    def test_create_defaults_str_and_url(self):
        job = make_job(self.core)
        self.assertEqual(str(job), "core: backup-test")
        self.assertIn("/plugins/guests/backup-jobs/", job.get_absolute_url())
        self.assertEqual(job.mode, BackupModeChoices.SNAPSHOT)
        self.assertEqual(job.notification_mode, BackupNotificationModeChoices.AUTO)
        self.assertTrue(job.enabled)
        self.assertFalse(job.repeat_missed)
        self.assertEqual(job.vmids, [])

    def test_vmids_are_derived_sorted_and_scoped_to_the_job(self):
        job = make_job(self.core)
        other = make_job(self.core, job_id="backup-other")
        make_profile("ct-b", self.core, 79255, job)
        make_profile("ct-a", self.core, 69250, job)
        make_profile("ct-c", self.core, 74234, other)
        make_profile("ct-none", self.core, 51100158)
        self.assertEqual(job.vmids, [69250, 79255])
        self.assertEqual(other.vmids, [74234])

    def test_job_id_unique_per_node_not_fleet_wide(self):
        make_job(self.core, job_id="backup-1")
        make_job(self.backup, job_id="backup-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_job(self.core, job_id="backup-1")

    def test_job_cannot_be_deleted_while_a_guest_relies_on_it(self):
        job = make_job(self.core)
        make_profile("ct-p", self.core, 101, job)
        with self.assertRaises(ProtectedError):
            job.delete()

    def test_node_cannot_be_deleted_under_its_jobs(self):
        node = make_device("doomed")
        make_job(node)
        with self.assertRaises(ProtectedError):
            node.delete()

    def test_mode_and_notification_mode_choices_are_validated(self):
        job = BackupJob(node=self.core, job_id="b", storage="pbs", schedule="21:00", mode="bogus")
        with self.assertRaises(ValidationError):
            job.full_clean()
        job = BackupJob(
            node=self.core, job_id="b", storage="pbs", schedule="21:00",
            mode=BackupModeChoices.SUSPEND,
            notification_mode=BackupNotificationModeChoices.NOTIFICATION_SYSTEM,
        )
        job.full_clean()


class GuestProfileBackupJobTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.core = make_device("core")
        cls.backup = make_device("backup")
        cls.job = make_job(cls.core)

    def _profile(self, **kwargs):
        return GuestProfile(
            virtual_machine=make_vm(kwargs.pop("name", "ct-x")),
            guest_type=GuestTypeChoices.CONTAINER, **kwargs,
        )

    def test_profile_on_the_jobs_node_with_a_vmid_is_valid(self):
        p = self._profile(vmid=200, node=self.core, backup_job=self.job)
        p.full_clean()
        p.save()
        self.assertEqual(self.job.vmids, [200])

    def test_job_on_another_node_is_rejected(self):
        p = self._profile(vmid=201, node=self.backup, backup_job=self.job)
        with self.assertRaisesMessage(ValidationError, "must run on this guest's node"):
            p.full_clean()

    def test_job_without_a_node_is_rejected(self):
        p = self._profile(vmid=202, backup_job=self.job)
        with self.assertRaisesMessage(ValidationError, "must run on this guest's node"):
            p.full_clean()

    def test_job_without_a_vmid_is_rejected(self):
        p = self._profile(node=self.core, backup_job=self.job)
        with self.assertRaisesMessage(ValidationError, "Set vmid"):
            p.full_clean()

    def test_no_job_is_valid(self):
        self._profile(vmid=203, node=self.backup).full_clean()
