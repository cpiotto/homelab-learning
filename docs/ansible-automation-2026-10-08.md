# Ansible automation lab - 8 October 2026

## Goal

Start the automation phase of the homelab by deploying a dedicated Ansible controller and using it to manage an existing Ubuntu Server VM over SSH.

The first target was VM 100 `ubuntu-server` on `pve3090`.

## Ansible controller

A new unprivileged Debian 13 LXC was created on `pve3080b`:

- VMID: 202
- Hostname: `ansible01`
- 2 vCPU
- 2 GB RAM
- 512 MB swap
- 8 GB root filesystem on `local-lvm`
- DHCP with router reservation
- Reserved IPv4 address: `192.168.1.121`
- Start at boot enabled
- Unprivileged container

The Debian 13.6 template was downloaded from the Proxmox template repository and its checksum was verified automatically.

After creation, the container was upgraded to the current Debian 13.7 package state.

## Systemd / nesting warning

Proxmox displayed:

```text
WARN: Systemd 257 detected. You may need to enable nesting.
```

The container started and operated correctly without nesting, so the feature was not enabled unnecessarily.

This follows the lab practice of making the smallest change required rather than enabling additional container permissions without a demonstrated need.

## Ansible installation

Ansible was installed from Debian repositories.

Verified versions:

```text
Ansible Core: 2.19.11
Python: 3.13.5
```

### Locale troubleshooting

The first `ansible --version` attempt failed with:

```text
ERROR: Ansible could not initialize the preferred locale: unsupported locale setting
```

The container was configured for `en_US.UTF-8`, but that locale had not yet been generated.

The `locales` package was already installed, so `en_US.UTF-8` was enabled in `/etc/locale.gen` and generated with `locale-gen`.

After the fix, `ansible --version` worked normally.

## Network validation

Before configuring Ansible, connectivity from `ansible01` to VM 100 was verified:

```text
ansible01 192.168.1.121
        |
        | LAN
        v
ubuntu-server 192.168.1.106
```

ICMP testing returned:

```text
3 packets transmitted
3 received
0% packet loss
```

A direct SSH test also confirmed that the SSH service was reachable before authentication was configured.

## SSH key authentication

An Ed25519 key pair dedicated to `ansible01` was created inside the controller.

Only the public key was copied to the `cesar` account on VM 100 using `ssh-copy-id`.

Afterwards:

```bash
ssh cesar@192.168.1.106
```

logged in without a password.

The private key remains only inside `ansible01` and is not stored in this repository.

## First inventory

The first inventory was created at:

```text
/root/ansible-lab/inventory.ini
```

Configuration:

```ini
[ubuntu]
ubuntu-server ansible_host=192.168.1.106 ansible_user=cesar ansible_python_interpreter=/usr/bin/python3.12
```

The Python interpreter was pinned explicitly after Ansible initially warned that interpreter auto-discovery could change in the future.

## First Ansible connectivity test

The first Ansible module test used:

```bash
ansible ubuntu -i inventory.ini -m ping
```

Result:

```text
ubuntu-server | SUCCESS
ping: pong
```

Ansible `ping` is not an ICMP ping. It verifies that Ansible can:

1. connect to the target over SSH
2. authenticate
3. execute Python remotely
4. receive a valid response

## First remote command

The controller then executed:

```bash
ansible ubuntu -i inventory.ini -m ansible.builtin.command -a "uptime"
```

VM 100 returned its system uptime and load averages successfully.

This was the first real remote administration task performed through Ansible.

## First playbook

The first playbook was created as:

```text
/root/ansible-lab/system-check.yml
```

It runs `uptime`, stores the result with `register`, marks the read-only command with `changed_when: false`, and prints the result with the debug module.

Execution:

```bash
ansible-playbook -i inventory.ini system-check.yml
```

Result:

```text
ok=2
changed=0
unreachable=0
failed=0
```

This demonstrated the difference between an ad-hoc Ansible command and a reusable YAML playbook.

## First privileged playbook

A second playbook was created:

```text
/root/ansible-lab/install-htop.yml
```

It uses:

- `become: true`
- the Ansible APT module
- `state: present`
- APT cache refresh

The playbook was executed with:

```bash
ansible-playbook -i inventory.ini install-htop.yml -K
```

The task returned:

```text
changed=0
```

because `htop` was already installed on VM 100.

A remote version check confirmed:

```text
htop 3.3.0
```

## Idempotence

This session introduced an important Ansible concept: **idempotence**.

Instead of blindly repeating installation commands, a declarative Ansible module checks the desired state.

For example:

```text
Desired state: htop installed
        |
        v
Ansible checks VM 100
        |
        v
htop already present
        |
        v
No change required
changed=0
```

This behaviour is one of the main reasons configuration-management tools are useful at scale.

## Current automation architecture

```text
pve3080b
└── LXC 202 ansible01
    ├── Debian 13
    ├── Ansible Core 2.19.11
    ├── SSH key authentication
    └── Inventory
          |
          | SSH
          v
      pve3090
      └── VM 100 ubuntu-server
          └── 192.168.1.106
```

## Skills practised

- LXC provisioning
- Debian package management
- locale troubleshooting
- Ansible installation
- SSH key authentication
- Ansible inventory
- Python interpreter selection
- Ansible ad-hoc commands
- Ansible modules
- YAML playbooks
- `register`
- `changed_when`
- privilege escalation with `become`
- declarative package management
- idempotence
- remote Linux administration

## Next steps

- add VM 101 to the Ansible inventory
- organise inventory groups and variables
- create a standard Linux baseline playbook
- automate package updates safely
- manage common packages and services
- practise user and SSH configuration
- use Ansible for Node Exporter or other repeatable service deployment
- later manage additional lab systems without changing critical infrastructure manually
