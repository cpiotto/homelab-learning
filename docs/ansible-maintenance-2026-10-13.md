# Ansible operational maintenance - 13 October 2026

## Goal

Create and validate a reusable operational maintenance playbook for the managed Ubuntu servers.

The objective was to combine the Ansible concepts learned in previous sessions into one practical workflow that can:

- refresh APT metadata
- apply available package upgrades
- detect whether a reboot is required
- reboot only when needed
- process one host at a time
- verify the running kernel after maintenance
- provide a concise maintenance summary

Managed hosts:

- `ubuntu-server` - VM 100 - `192.168.1.106`
- `ubuntu-server-01` - VM 101 - `192.168.1.111`

Controller:

- `ansible01` - LXC 202 on `pve3080b`

## 1. Created maintenance.yml

A new playbook was created at:

```text
/root/ansible-lab/maintenance.yml
```

Core structure:

```yaml
---
- name: Maintain Ubuntu servers safely
  hosts: ubuntu
  become: true
  gather_facts: false
  serial: 1
```

The use of:

```yaml
serial: 1
```

ensures only one managed server is maintained at a time.

This reduces risk by preventing simultaneous reboots across the Ubuntu group.

## 2. Maintenance workflow

The playbook performs the following sequence:

1. capture the running kernel
2. refresh APT cache
3. upgrade installed packages
4. check `/var/run/reboot-required`
5. reboot only if required
6. wait for the server to return
7. capture the running kernel again
8. display a maintenance summary
9. continue to the next host

The package upgrade task uses the Ansible APT module rather than shelling out to the `apt` CLI.

## 3. Dry-run validation

Before applying updates, the playbook was tested with:

```bash
ansible-playbook -i inventory.ini maintenance.yml -K --check
```

The first dry run exposed an important behaviour: Ansible's `command` module does not normally execute in check mode.

As a result, the kernel fields were initially empty.

The two read-only kernel checks were updated with:

```yaml
check_mode: false
```

This explicitly allows `uname -r` to run even when the rest of the playbook is in dry-run mode.

A second check-mode execution then correctly reported:

```text
Kernel before: 6.8.0-146-generic
Kernel after:  6.8.0-146-generic
Packages changed: True
Reboot required: False
```

This showed that package changes were available while the dry run itself made no real system changes.

## 4. Real maintenance execution

The playbook was then executed normally:

```bash
ansible-playbook -i inventory.ini maintenance.yml -K
```

Available package updates were installed.

The upgrade introduced a newer Ubuntu kernel.

The maintenance summary for the managed hosts showed the kernel transition:

```text
6.8.0-146-generic
        |
        v
6.8.0-147-generic
```

The playbook also detected that a reboot was required after the package upgrade and handled the restart automatically.

Because `serial: 1` was enabled, one VM was fully processed and validated before Ansible moved to the next VM.

## 5. Post-maintenance reboot validation

After the maintenance playbook completed, the existing `reboot-check.yml` playbook was executed again.

Both hosts reported:

```text
does not require a reboot
```

This confirmed that the new kernel was active and the reboot requirement had been cleared.

## 6. Package-state validation

A final read-only check was performed with:

```bash
ansible ubuntu -i inventory.ini \
  -m ansible.builtin.command -a "apt list --upgradable"
```

Both hosts returned only:

```text
Listing...
```

with no packages listed afterwards.

This confirmed that no additional package upgrades remained pending at the end of the maintenance session.

The warning about the `apt` CLI not being stable for scripting was noted. The maintenance playbook itself correctly uses `ansible.builtin.apt` for automation.

## Result

Both managed Ubuntu VMs finished the session:

- fully updated
- running kernel `6.8.0-147-generic`
- with no reboot pending
- reachable through Ansible
- with no remaining package upgrades

The operational maintenance workflow is now reusable for future Ubuntu hosts added to the `ubuntu` inventory group.

## Current automation flow

```text
ansible01
    |
    v
ubuntu group
    |
    |-- ubuntu-server
    |      |
    |      |-- APT update
    |      |-- package upgrade
    |      |-- reboot if required
    |      '-- validation
    |
    '-- ubuntu-server-01
           |
           |-- APT update
           |-- package upgrade
           |-- reboot if required
           '-- validation
```

## Skills practised

- operational Ansible playbooks
- safe package maintenance
- Ansible check mode
- overriding check mode for read-only commands
- APT package management
- conditional reboot
- sequential maintenance with `serial: 1`
- kernel validation
- post-maintenance checks
- reusable infrastructure operations

## Next step

The next stage is to expand Ansible beyond the two Ubuntu VMs by adding infrastructure systems such as `dns01` and `monitor01` into dedicated inventory groups and managing them with role-appropriate automation.
