# PVE-02 / Dell OptiPlex 3090 Storage Troubleshooting

Date: 14 September 2026

This document records a storage troubleshooting session on the Dell OptiPlex 3090 Proxmox node. The goal was to test different storage options, understand why an NVMe device was not being detected, and leave the node in a stable and remotely manageable state.

## Node details

| Item | Value |
| --- | --- |
| Hardware | Dell OptiPlex 3090 Micro |
| Hostname | `pve3090` |
| Role | Secondary Proxmox VE node |
| Management IP | `192.168.1.165/24` |
| Proxmox web UI | `https://192.168.1.165:8006` |
| Working system disk | Samsung SSD 840 Series SATA |
| Detected capacity | 111.8 GB |
| BIOS storage mode observed | RAID On |

## Objective

The session focused on:

- Testing a SATA SSD as a Proxmox system disk.
- Testing whether an NVMe/Kioxia device could be detected.
- Verifying the storage layout from Linux.
- Checking BIOS and boot behaviour.
- Avoiding unnecessary BIOS changes while the system was already working reliably from SATA.
- Returning the OptiPlex to a headless state that can be administered remotely.

## Working SATA configuration

Proxmox successfully booted from the Samsung SSD 840 Series SATA drive.

The storage devices were checked with:

```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

The working system disk appeared as:

```text
sda                111.8G Samsung SSD 840 Series sata
├─sda1              1007K
├─sda2                 1G
└─sda3             110.8G
  ├─pve-swap           8G
  ├─pve-root        37.7G
  ├─pve-data_tmeta     1G
  │ └─pve-data      49.3G
  └─pve-data_tdata  49.3G
    └─pve-data      49.3G
```

This confirmed both the physical disk and the Proxmox LVM layout.

## NVMe / Kioxia detection test

A Kioxia NVMe SSD was also tested during the session.

The expected device did not appear in `lsblk`, while the Samsung SATA SSD remained visible. This showed that the problem was below the Proxmox storage configuration layer: Linux was not seeing the NVMe device as an available block device.

Troubleshooting steps included:

- Rechecking the physical installation and connections.
- Rebooting the OptiPlex.
- Inspecting the Dell boot menu.
- Checking BIOS storage settings.
- Comparing the BIOS-visible devices with the devices detected by Linux.
- Re-running storage detection commands after boot.

The NVMe device was not detected during this session.

## BIOS investigation

The Dell BIOS showed the storage mode set to:

```text
RAID On
```

Some BIOS settings were restricted, limiting the ability to freely change the storage controller configuration.

Because Proxmox was already operating correctly from the Samsung SATA SSD, the decision was made not to force a controller-mode change simply to make the NVMe experiment work.

This avoided risking a working Proxmox installation for an unproven storage configuration.

## Final decision

The Samsung SSD 840 Series SATA drive was retained as the current Proxmox system disk.

The OptiPlex was closed and returned to normal operation with remote administration available over the network.

Current management address:

```text
192.168.1.165
```

The NVMe issue remains a separate troubleshooting task and can be revisited later without affecting the working SATA installation.

## Troubleshooting logic

The session reinforced an important troubleshooting sequence:

1. Confirm what the operating system can actually detect.
2. Use `lsblk` before assuming a Proxmox configuration problem.
3. Compare Linux detection with BIOS/boot detection.
4. Check physical installation before changing software settings.
5. Avoid changing controller modes on a working installation without a clear recovery plan.
6. Preserve a known-good configuration before continuing experiments.

## Skills practised

- Linux block-device identification
- SATA and NVMe storage concepts
- Proxmox LVM layout
- Dell BIOS and boot-menu navigation
- Hardware versus software fault isolation
- Risk-based troubleshooting
- Headless Proxmox administration
- Infrastructure documentation

## Commands used

```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

The session also involved normal reboot, boot-menu and BIOS checks while comparing what the firmware and Linux could detect.

## Outcome

The node ended the session in a stable state:

- Proxmox boots from the Samsung SATA SSD.
- The Proxmox LVM volumes are present.
- The node remains reachable at `192.168.1.165`.
- The machine no longer requires a permanently attached monitor or keyboard for routine administration.
- The NVMe/Kioxia detection issue is documented for future investigation.

## Follow-up

- Keep the Samsung SATA SSD as the known-good boot device for now.
- Revisit NVMe support only when a compatible connection path or BIOS option can be tested safely.
- Consider a larger SATA SSD later if more local storage is required.
- Configure backups before placing important workloads on the node.
