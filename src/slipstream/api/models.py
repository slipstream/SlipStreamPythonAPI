from __future__ import unicode_literals

import collections

App = collections.namedtuple('App', [
    'name',
    'type',
    'version',
    'path',
])

Deployment = collections.namedtuple('Deployment', [
    'id',
    'module',
    'status',
    'started_at',
    'last_state_change',
    'clouds',
    'username',
    'abort',
    'service_url',
    'scalable',
])

Node = collections.namedtuple('Node', [
    'path',
    'name',
    'cloud',
    'multiplicity',
    'max_provisioning_failures',
    'network',
    'cpu',
    'ram',
    'disk',
    'extra_disk_volatile',
])

VirtualMachine = collections.namedtuple('VirtualMachine', [
    'id',
    'cloud',
    'status',
    'deployment_id',
    'deployment_owner',
    'node_name',
    'node_instance_id',
    'ip',
    'cpu',
    'ram',
    'disk',
    'instance_type',
    'is_usable',
])

Usage = collections.namedtuple('Usage', [
    'cloud',
    'run_usage',
    'vm_usage',
    'inactive_vm_usage',
    'others_vm_usage',
    'pending_vm_usage',
    'unknown_vm_usage',
    'quota',
])

Module = collections.namedtuple('Module', [
    'name',
    'type',
    'created',
    'modified',
    'description',
    'version',
    'path',
])

User = collections.namedtuple('User', [
    'username',
    'cyclone_login',
    'github_login',
    'email',
    'first_name',
    'last_name',
    'organization',
    'configured_clouds',
    'default_cloud',
    'ssh_public_keys',
    'keep_running',
    'timeout',
    'privileged',
])

