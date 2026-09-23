# Lenovo V520s Storage Upgrade and Cleanup

Date: 23 September 2026

This document records a storage reorganisation and cleanup session on the Lenovo ThinkCentre V520s Proxmox node. The goal was to make better use of the available SSDs, create dedicated VM/container storage and backup storage, verify disk health, and remove an obsolete LXC disk before rebuilding the container environment cleanly.

## Node details

| Item | Value |
| --- | --- |
| Hardware | Lenovo ThinkCentre V520s |
| Hostname | `pve` |
| Role | Proxmox VE virtualization / storage lab node |
| Management IP | `192.168.1.164/24` |
| Proxmox VE | 9.2.20 |
| Running kernel | `7.0.14-17-pve` |

## Final physical storage layout

| Linux device | Drive | Purpose |
| --- | --- | --- |
| `/dev/sdb` | Samsung SSD 830 256 GB SATA | Existing Proxmox system disk |
| `/dev/nvme0n1` | Samsung PM991a 256 GB NVMe | Dedicated Proxmox thin storage for VMs/LXC |
| `/dev/sda` | Samsung MZ7LN256HCHP 256 GB SATA | Secondary backup / ISO / template storage |

The session changed the Lenovo from a mostly single-disk Proxmox system into a node with separate storage roles.

## Boot and hardware investigation

After the additional drives were installed, the Lenovo BIOS initially showed the Samsung PM991a NVMe with Windows Boot Manager while the SATA Proxmox disk did not appear as a normal boot choice.

The BIOS SATA controller and ports were checked and AHCI was enabled. The boot order was also reviewed.

Because changing or formatting the working Proxmox disk would have created unnecessary risk, the troubleshooting approach was to preserve the existing SATA installation and verify the hardware layout before making storage changes.

Proxmox was subsequently available again from the existing SATA system disk.

## NVMe reuse for Proxmox

The Samsung PM991a 256 GB NVMe previously contained an old Windows / BitLocker installation that was no longer needed.

The old content was removed and the NVMe was repurposed as a Proxmox LVM-thin storage pool named:

```text
nvme-storage
```

It was configured for virtual machine and LXC container disks.

The storage was verified with:

```bash
pvesm status
```

Observed capacity:

```text
nvme-storage  249810944 KiB
```

At the end of the configuration it was active and unused, ready for new workloads.

## Secondary SATA SSD health check

The Samsung MZ7LN256HCHP 256 GB SATA SSD was tested before being assigned a role.

SMART checks showed:

- Overall SMART result passed.
- No reallocated sectors were reported.
- No uncorrectable errors were reported.
- No CRC errors were reported.
- Temperature was approximately 27°C.
- The extended SMART self-test completed without error.
- The drive had approximately 66,065 power-on hours.
- SMART attribute 9 was flagged as `FAILING_NOW`.

Because of the very high accumulated operating time, the drive was not selected as the only location for important data. It is being used as secondary lab backup/storage rather than trusted primary storage.

The extended test result was checked with:

```bash
smartctl -l selftest /dev/sda
```

## Backup storage configuration

A partition was created on the secondary SATA SSD, formatted as EXT4 and mounted at:

```text
/mnt/pve-backup
```

The storage was then added to Proxmox as:

```text
backup-storage
```

The filesystem showed approximately:

```text
234G total
222G available
```

The filesystem UUID was added to `/etc/fstab` so the mount can persist across reboots.

Configured UUID:

```text
0fb900cf-a715-45c8-98f8-b0a73e47db70
```

The Proxmox storage status later showed the backup storage active with approximately:

```text
245023328 KiB
```

This storage is intended for items such as:

- Proxmox backups
- ISO images
- Container templates
- Lab files that do not require primary-grade storage

## LXC 100 cleanup

The Lenovo still had an old LXC 100 workload associated with the previous `docker01` environment.

During the cleanup, the container was found still running:

```bash
lxc-info -n 100
```

The container was stopped before its old storage was removed.

The remaining volume was an orphaned LVM-thin disk because the normal LXC configuration file was no longer present.

The obsolete disk was removed with:

```bash
pvesm free local-lvm:vm-100-disk-0
```

After removal:

```bash
pvesm list local-lvm
```

returned no remaining VM/LXC volumes on `local-lvm`.

The decision was to rebuild `docker01` cleanly later instead of carrying forward the old container state.

## Final Proxmox storage state

At the end of the session the Lenovo had four Proxmox storage roles available:

- `local` — directory storage on the Proxmox system disk
- `local-lvm` — existing LVM-thin storage, now empty after cleanup
- `nvme-storage` — dedicated 256 GB NVMe LVM-thin pool for new VM/LXC disks
- `backup-storage` — dedicated 256 GB SATA EXT4 storage for backups, ISOs and templates

This gives the node a much clearer separation between:

1. Operating system storage
2. VM/container storage
3. Backup and installation-media storage

## Commands practised

```bash
lsblk
lsblk -f
smartctl
smartctl -l selftest /dev/sda
pvesm status
pvesm list local-lvm
pvesm free local-lvm:vm-100-disk-0
lxc-info -n 100
lxc-stop -n 100
df -h
findmnt
blkid
```

## Skills practised

- Physical SSD installation and identification
- SATA versus NVMe storage roles
- Proxmox storage planning
- LVM-thin storage configuration
- EXT4 filesystem preparation
- Persistent Linux mounts with `/etc/fstab`
- SMART health analysis
- Safe handling of an ageing SSD
- LXC storage cleanup
- Orphaned volume identification
- Separating system, workload and backup storage
- BIOS and boot troubleshooting
- Infrastructure documentation

## Outcome

The Lenovo V520s ended the session with a cleaner and more flexible storage layout:

- Existing Proxmox installation preserved on the Samsung SSD 830 SATA disk.
- Samsung PM991a NVMe repurposed as `nvme-storage`.
- Samsung MZ7LN256HCHP SATA SSD configured as `backup-storage`.
- Extended SMART test completed successfully on the backup SSD, with its high operating hours documented as a limitation.
- Old LXC 100 storage removed from `local-lvm`.
- `local-lvm` left empty and ready for future use.
- Dedicated storage is now available for new VMs and LXC containers.
- The old `docker01` environment can be rebuilt cleanly rather than migrated with stale state.

## Next steps

- Reboot-test the persistent `/mnt/pve-backup` mount.
- Rebuild `docker01` using the new storage layout.
- Create and test a Proxmox backup job.
- Verify restore procedures before relying on the backup workflow.
- Continue monitoring SMART data on the high-hours SATA backup SSD.
