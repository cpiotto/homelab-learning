# Ansible conditions and rolling maintenance - 10 October 2026

## Goal

Continue the Ansible learning path by introducing conditional execution and then applying it to a real maintenance workflow.

The session progressed from simple `when` conditions to reboot detection, kernel validation and a reusable rolling reboot playbook.

Managed hosts:

- `ubuntu-server` - VM 100 - `192.168.1.106`
- `ubuntu-server-01` - VM 101 - `192.168.1.111`

Both are managed from LXC 202 `ansible01` on `pve3080b`.

## 1. Conditions based on inventory hostname

A new playbook, `conditions-demo.yml`, was created to demonstrate host-specific conditional execution.

Example:

```yaml
when: inventory_hostname == "ubuntu-server"
```

The playbook showed that:

- the matching task runs with `ok`
- the non-matching task is marked `skipped`

Each host finished with one skipped task, proving that Ansible evaluated the condition independently for every managed host.

## 2. Conditions based on Ansible Facts

A second playbook, `conditions-facts.yml`, used facts collected from the remote systems.

Conditions tested:

```yaml
when:
  - ansible_facts['distribution'] == "Ubuntu"
  - ansible_facts['distribution_major_version'] == "24"
```

and:

```yaml
when: ansible_facts['memtotal_mb'] < 3000
```

Both hosts matched the Ubuntu 24 condition and the low-memory condition because each VM currently has about 2 GB RAM.

The playbook was read-only and completed with `changed=0`.

## 3. Reboot-required detection

A new playbook, `reboot-check.yml`, was created using the `stat` module:

```yaml
- name: Check reboot-required file
  ansible.builtin.stat:
    path: /var/run/reboot-required
  register: reboot_required
```

Conditional messages were then selected with:

```yaml
when: reboot_required.stat.exists
```

and:

```yaml
when: not reboot_required.stat.exists
```

Both VMs reported that a reboot was required.

## 4. Identifying the reason for reboot

The file:

```text
/var/run/reboot-required.pkgs
```

showed:

```text
linux-image-6.8.0-146-generic
linux-base
```

The running kernel was then checked with:

```bash
uname -r
```

Both VMs were still running:

```text
6.8.0-142-generic
```

This confirmed that a newer kernel had already been installed but had not yet been loaded.

## 5. Pre-reboot session check

Before rebooting, active logins were inspected using `who` and `w`.

The sessions found were either:

- temporary Ansible SSH connections from `ansible01`
- an idle console session on VM 101

No important interactive workload was found, so maintenance could proceed safely.

## 6. Controlled reboot one host at a time

The first reboot was intentionally limited to VM 100:

```bash
ansible ubuntu-server -i inventory.ini -b -K \
  -m ansible.builtin.reboot -a "reboot_timeout=300"
```

Result:

```text
rebooted: true
elapsed: 14
```

After the VM returned, the active kernel was verified as:

```text
6.8.0-146-generic
```

Only after VM 100 had been validated was VM 101 rebooted.

VM 101 returned successfully in approximately 15 seconds and also loaded:

```text
6.8.0-146-generic
```

This demonstrated a safer maintenance method than rebooting all managed hosts simultaneously.

## 7. Post-maintenance validation

The `reboot-check.yml` playbook was executed again after both VMs returned.

Both hosts reported:

```text
does not require a reboot
```

The reboot-warning task was skipped and the play completed with:

```text
changed=0
failed=0
unreachable=0
```

## 8. Rolling reboot playbook

A reusable playbook named `rolling-reboot.yml` was created.

Important elements:

```yaml
hosts: ubuntu
become: true
gather_facts: false
serial: 1
```

The `serial: 1` setting means Ansible processes only one host at a time.

The playbook:

1. records the current kernel
2. checks `/var/run/reboot-required`
3. reboots only when required
4. waits for the server to return
5. records the kernel after maintenance
6. displays a maintenance summary

The reboot task is conditional:

```yaml
when: reboot_required.stat.exists
```

Because both VMs had already been rebooted during the session, the first full test of `rolling-reboot.yml` correctly skipped the reboot task on both hosts and returned `changed=0`.

## Maintenance logic

```text
Host 1
  |
  |-- reboot required? -- no --> validate --> continue
  |
  '-- yes --> reboot --> wait for return --> validate
                                      |
                                      v
                                   Host 2
                                      |
                                      '-- repeat
```

This creates the foundation for controlled rolling maintenance as more Ubuntu systems are added to the Ansible inventory.

## Skills practised

- `when`
- host-specific conditions
- conditions based on Ansible Facts
- multiple conditions
- numerical comparisons
- `stat`
- `register`
- conditionally skipped tasks
- reboot-required detection
- Linux kernel version validation
- checking active user sessions before maintenance
- Ansible `reboot` module
- post-reboot validation
- `serial: 1`
- rolling maintenance
- safe one-host-at-a-time operations
- reusable maintenance playbooks

## Current Ansible playbooks

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
├── install-htop.yml
├── conditions-demo.yml
├── conditions-facts.yml
├── reboot-check.yml
└── rolling-reboot.yml
```

## Next step

The next stage is to move from learning individual Ansible concepts toward a more complete operational maintenance workflow, such as safe package updates, validation and reusable automation for additional homelab systems.
