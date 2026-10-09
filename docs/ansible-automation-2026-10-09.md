# Ansible multi-host management session - 9 October 2026

## Goal

Continue the Ansible learning path by moving from single-host automation to multi-host management, reusable variables, system auditing, configuration management and handlers.

The session focused on VM 100 `ubuntu-server` and VM 101 `ubuntu-server-01` on `pve3090`.

## 1. Added VM 101 to Ansible

Connectivity from `ansible01` to VM 101 at `192.168.1.111` was verified successfully with ICMP.

Before trusting the SSH host key, the ED25519 fingerprint presented to `ansible01` was compared directly with the fingerprint generated on VM 101. The values matched, so the host key was accepted safely.

An Ed25519 public key from `ansible01` was then copied to the `cesar` account on VM 101 with `ssh-copy-id`.

Passwordless SSH was validated before adding the host to Ansible.

## 2. Multi-host inventory

The Ansible inventory was expanded from one managed Ubuntu VM to two:

```ini
[ubuntu]
ubuntu-server ansible_host=192.168.1.106
ubuntu-server-01 ansible_host=192.168.1.111
```

Both hosts returned:

```text
SUCCESS
ping: pong
```

A previously created `system-check.yml` playbook was then executed against the whole `ubuntu` group, proving that a single playbook can manage multiple systems in parallel.

## 3. System audit with Ansible Facts

A new playbook, `system-audit.yml`, was created using:

```yaml
gather_facts: true
```

The playbook collected and displayed structured facts including:

- hostname
- Ubuntu version
- kernel
- architecture
- vCPU count
- memory
- primary IPv4 address

The two VMs reported:

| Host | IPv4 | OS | Kernel | vCPU | RAM |
| --- | --- | --- | --- | ---: | ---: |
| ubuntu-server | 192.168.1.106 | Ubuntu 24.04 | 6.8.0-142-generic | 2 | 1967 MB |
| ubuntu-server-01 | 192.168.1.111 | Ubuntu 24.04 | 6.8.0-142-generic | 2 | 1967 MB |

## 4. Hostname inconsistency discovered

The audit exposed a real configuration issue.

The actual hostnames were:

```text
unbuntu-server
unbuntu-server-01
```

instead of:

```text
ubuntu-server
ubuntu-server-01
```

The same typo existed in both `/etc/hostname` and the `127.0.1.1` entry in `/etc/hosts`.

Before making changes, backups of both files were created on both VMs.

## 5. Hostname correction playbook

A reusable playbook named `fix-hostnames.yml` was created.

It uses the inventory host name as the desired system hostname:

```yaml
name: "{{ inventory_hostname }}"
```

The playbook:

- sets the system hostname
- updates the matching line in `/etc/hosts`
- creates a backup before editing `/etc/hosts`

The first execution reported two changes per server.

A second execution reported:

```text
changed=0
failed=0
```

This demonstrated idempotence with a real system configuration rather than only a package-state example.

## 6. Ubuntu baseline playbook

A new `baseline.yml` playbook was created to define a common package baseline:

```yaml
baseline_packages:
  - curl
  - git
  - htop
  - unzip
  - rsync
```

The playbook also refreshes the APT cache when required.

The first run installed missing packages and updated the cache.

The second run returned:

```text
changed=0
```

on both VMs, confirming that the desired package state was already satisfied.

## 7. Group variables

Common host settings were moved out of individual inventory lines into:

```text
/root/ansible-lab/group_vars/ubuntu.yml
```

Contents:

```yaml
---
ansible_user: cesar
ansible_python_interpreter: /usr/bin/python3.12
```

This removed duplication from `inventory.ini` and made the project easier to scale.

After the change, `ansible -m ping` still succeeded on both hosts.

The inventory graph was also verified with:

```bash
ansible-inventory -i inventory.ini --graph
```

Result:

```text
@ubuntu
├── ubuntu-server
└── ubuntu-server-01
```

## 8. Handlers and notify

A demonstration playbook named `service-demo.yml` was created using the `cron` service.

The playbook ensures:

- the `cron` package is installed
- the service is running and enabled
- a managed file exists at `/etc/cron.d/ansible-demo`

The file task uses:

```yaml
notify: Restart cron
```

The handler only restarts `cron` when the configuration file changes.

On the first run:

- the file was created
- the handler ran
- `cron` restarted

On the second run:

- all tasks returned `ok`
- `changed=0`
- the handler did not run

This demonstrated event-driven service management and safe idempotent behaviour.

## Current project structure

```text
/root/ansible-lab/
├── inventory.ini
├── inventory.ini.bak
├── group_vars/
│   └── ubuntu.yml
├── system-check.yml
├── system-audit.yml
├── fix-hostnames.yml
├── baseline.yml
├── service-demo.yml
└── install-htop.yml
```

## Skills practised

- SSH host-key verification
- passwordless SSH with `ssh-copy-id`
- multi-host Ansible inventory
- parallel management of multiple systems
- Ansible Facts
- variables
- `group_vars`
- hostname management
- `lineinfile`
- backup before configuration changes
- reusable baseline playbooks
- package-state management
- idempotence
- service management
- `notify`
- handlers
- inventory graph inspection

## Next step

The next Ansible session will introduce conditional execution with `when`, allowing tasks to run only when specific facts, hostnames, distributions or other conditions are met.
