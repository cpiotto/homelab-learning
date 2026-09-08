# Homelab Learning

This repository documents my practical learning journey with Linux, networking, virtualization and containerization.

## Lab Hardware

- Lenovo ThinkCentre V520s
- Intel Core i5-7400
- 16 GB RAM
- 256 GB SSD

## Technologies

- Proxmox VE
- Debian Linux
- LXC Containers
- Docker
- Docker Compose
- Networking
- Linux administration

## Current Architecture


```text
Lenovo ThinkCentre V520s
└── Proxmox VE
    └── LXC 100 - docker01
        └── Debian 13
            └── Docker
                └── Portainer
                    └── portainer_data volume
```

## Learning Goals

The goal of this homelab is to develop practical skills in:

- Linux administration
- Networking
- Virtualization
- Docker and containers
- Troubleshooting
- Cybersecurity
- Server administration

## Current Progress

- [x] Installed Proxmox VE
- [x] Configured Proxmox no-subscription repository
- [x] Updated Proxmox
- [x] Upgraded homelab to 16 GB RAM
- [x] Created Debian 13 LXC container
- [x] Configured networking with DHCP
- [x] Installed Docker repository
- [x] Installed Docker Engine
- [x] Verified Docker service
- [x] Ran first Docker container (hello-world)
- [x] Learned Docker images, containers and logs
- [x] Created first persistent Docker volume
- [x] Installed and configured Portainer
- [x] Managed containers through Portainer
- [ ] Deploy first additional homelab service
