# First Ubuntu Server VM on PVE-02 - 15 September 2026

This session created and validated the first full virtual machine on the Dell OptiPlex 3090 Proxmox node. The goal was to connect the VM to the existing LAN through `vmbr0`, install Ubuntu Server, enable remote administration, integrate the QEMU Guest Agent, reserve a predictable IP address and verify that the guest survives a reboot cleanly.

## Final VM state

| Item | Value |
| --- | --- |
| Proxmox node | `pve3090` / PVE-02 |
| VM ID | `100` |
| VM name | `ubuntu-server` |
| Guest OS | Ubuntu Server 24.04.5 LTS |
| vCPU | 2 cores |
| Memory | 2048 MiB |
| Virtual disk | 20 GiB |
| Disk storage | `local-lvm` |
| ISO storage | `local` |
| Network model | VirtIO |
| Proxmox bridge | `vmbr0` |
| Guest interface | `ens18` |
| MAC address | `BC:24:11:47:01:A7` |
| IPv4 address | `192.168.1.106/24` |
| Gateway | `192.168.1.254` |
| Addressing | DHCP with router reservation |
| SSH | Enabled and tested |
| QEMU Guest Agent | Installed, active and tested |
| Start at boot | Enabled |

## Architecture

```text
Home LAN 192.168.1.0/24
        |
        +-- Lenovo V520s / PVE-01
        |      192.168.1.164
        |
        +-- OptiPlex 3090 / PVE-02
               192.168.1.165
                    |
                  nic0
                    |
                  vmbr0
                    |
             VirtIO network
                    |
             VM 100 ubuntu-server
             192.168.1.106
```

The VM is therefore not isolated inside Proxmox. It appears on the same LAN as the physical Proxmox hosts and can be reached directly from other systems on the network.

## ISO and VM creation

The Ubuntu Server ISO was downloaded directly into Proxmox `local` storage:

```text
ubuntu-24.04.5-live-server-amd64.iso
```

The VM was created as:

```text
VM ID: 100
Name: ubuntu-server
CPU: 2 vCPU
RAM: 2048 MiB
Disk: 20 GiB
Disk storage: local-lvm
Network: VirtIO on vmbr0
QEMU Agent option: enabled
```

This reinforced the Proxmox storage distinction:

```text
local      -> ISO images, templates and backups
local-lvm  -> VM and LXC virtual disks
```

## Ubuntu installation

The standard Ubuntu Server installation was selected rather than the minimized installation.

During setup:

- language was set to English
- third-party drivers were not selected
- DHCP automatically assigned `192.168.1.106/24`
- no HTTP proxy was configured
- the default UK Ubuntu archive mirror passed connectivity tests
- the OpenSSH Server package was selected
- Ubuntu Pro was skipped
- optional featured snaps were not installed

### Storage layout

The installer created an LVM-based guest layout. The root logical volume was increased from the default 10 GiB allocation to 16 GiB so the server has more room for packages, logs and future lab tools.

The virtual disk remained 20 GiB.

## Network validation

During installation the guest received:

```text
Interface: ens18
IPv4: 192.168.1.106/24
Gateway: 192.168.1.254
```

The routing table later confirmed:

```text
default via 192.168.1.254 dev ens18 proto dhcp src 192.168.1.106
192.168.1.0/24 dev ens18 proto kernel scope link src 192.168.1.106
```

The guest Netplan configuration remained DHCP-based:

```yaml
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: true
```

Rather than manually assigning a static address inside Ubuntu, the router was checked and confirmed to have a DHCP reservation for the VM:

```text
Device: ubuntu-server
MAC: BC:24:11:47:01:A7
Reserved IP: 192.168.1.106
Always use this IP address: YES
```

This keeps gateway and DNS management simple while giving the VM a predictable address.

## Console troubleshooting

After installation and reboot, the Proxmox noVNC console initially appeared completely black.

Instead of reinstalling the guest, the VM was investigated layer by layer.

The host confirmed that the VM was running:

```bash
qm status 100
```

The configuration confirmed the virtual disk and boot order:

```bash
qm config 100
qm config 100 | grep scsi0
```

Observed configuration included:

```text
boot: order=scsi0;ide2;net0
scsi0: local-lvm:vm-100-disk-0,iothread=1,size=20G
ide2: none,media=cdrom
```

The guest also responded to ICMP at `192.168.1.106`, proving the operating system was alive even though the console display was blank.

A VM reset was performed:

```bash
qm reset 100
```

The console then displayed the normal Ubuntu login prompt:

```text
Ubuntu 24.04.5 LTS ubuntu-server tty1
ubuntu-server login:
```

This was a useful troubleshooting lesson: a blank virtual console does not automatically mean that the guest OS has failed.

## SSH troubleshooting and activation

Initial SSH attempts reached the guest network address but port 22 was not accepting connections.

Inside Ubuntu, the SSH service state was checked:

```bash
sudo systemctl is-active ssh
```

It returned:

```text
inactive
```

The service was then enabled and started:

```bash
sudo systemctl enable --now ssh
```

Verification:

```bash
sudo systemctl is-active ssh
```

returned:

```text
active
```

SSH access then worked from both the PVE-02 host and the Lenovo PVE-01 node:

```bash
ssh cesar@192.168.1.106
```

The VM was therefore successfully administered across the LAN from another physical Proxmox host.

Verbose SSH diagnostics were also practised with:

```bash
ssh -vvv cesar@192.168.1.106
```

This helped show the authentication sequence and demonstrated that password entry in Linux does not display characters or asterisks while typing.

## QEMU Guest Agent

The Proxmox VM option for QEMU Guest Agent was enabled at VM creation time, but the package still had to be installed inside Ubuntu.

Installation:

```bash
sudo apt install qemu-guest-agent -y
```

The service was started and checked:

```bash
sudo systemctl start qemu-guest-agent
sudo systemctl is-active qemu-guest-agent
```

The Proxmox host then successfully communicated with the guest:

```bash
qm agent 100 ping
```

Guest network information was queried directly through the agent:

```bash
qm guest cmd 100 network-get-interfaces
```

This returned the expected guest interface information, including:

```text
ens18
MAC: bc:24:11:47:01:a7
IPv4: 192.168.1.106/24
```

The practical distinction is:

```text
SSH              -> administrator connects to the guest over the network
QEMU Guest Agent -> Proxmox communicates with the guest through the hypervisor integration channel
```

## Automatic startup and reboot validation

`Start at boot` was enabled for VM 100 in Proxmox so the Ubuntu server will start automatically when PVE-02 boots.

The guest was then rebooted from the Proxmox host:

```bash
qm reboot 100
```

After reboot, the following were confirmed:

- VM status returned to `running`
- reserved IPv4 address remained `192.168.1.106`
- SSH access worked
- QEMU Guest Agent responded

The `Start at boot` behaviour itself will be naturally confirmed the next time the physical PVE-02 host is restarted.

## Commands practised

```bash
qm status 100
qm config 100
qm config 100 | grep scsi0
qm config 100 | grep net0
qm reset 100
qm reboot 100
qm agent 100 ping
qm guest cmd 100 network-get-interfaces
ip route
ls /etc/netplan/
sudo cat /etc/netplan/50-cloud-init.yaml
sudo systemctl is-active ssh
sudo systemctl enable --now ssh
sudo apt install qemu-guest-agent -y
sudo systemctl start qemu-guest-agent
sudo systemctl is-active qemu-guest-agent
ssh cesar@192.168.1.106
ssh -vvv cesar@192.168.1.106
```

## Key lessons

1. `vmbr0` allows virtual guests to participate directly in the physical LAN through the host NIC.
2. ISO storage and VM disk storage are separate Proxmox storage roles even when they use the same physical SSD.
3. A guest can be fully alive on the network even if the noVNC console appears blank.
4. Selecting OpenSSH during installation does not guarantee the service is already active after first boot; verify it with `systemctl`.
5. Enabling QEMU Guest Agent in Proxmox and installing `qemu-guest-agent` inside the guest are both required.
6. DHCP reservation is a practical way to give a server a predictable address without hard-coding gateway and DNS settings in the guest.
7. Troubleshooting is more reliable when each layer is tested separately: VM state, virtual disk, boot order, ICMP, TCP/SSH, service state and hypervisor integration.

## Result

PVE-02 now hosts its first fully operational VM:

```text
VM 100 - ubuntu-server
Ubuntu Server 24.04.5 LTS
2 vCPU / 2 GB RAM / 20 GiB disk
192.168.1.106
SSH: working
QEMU Guest Agent: working
DHCP reservation: working
Start at boot: enabled
```

This marks the transition of PVE-02 from a newly recovered Proxmox host into an active virtualization node that can host lab services and future workloads.
