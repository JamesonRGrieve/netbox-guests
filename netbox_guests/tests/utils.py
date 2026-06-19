# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared test helpers. ``make_vm`` builds a core virtualization VM (the parent every GuestMount
needs) via an idempotent ClusterType/Cluster, so each test module gets a guest without repeating
the cluster boilerplate."""
from virtualization.models import Cluster, ClusterType, VirtualMachine


def make_vm(name, cluster_name="core"):
    ctype, _ = ClusterType.objects.get_or_create(name="PVE", slug="pve")
    cluster, _ = Cluster.objects.get_or_create(name=cluster_name, type=ctype)
    return VirtualMachine.objects.create(name=name, cluster=cluster)
