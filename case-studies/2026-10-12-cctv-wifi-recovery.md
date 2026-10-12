# Real-World IT Support Case Study: Restoring CCTV After a Router Replacement

**Date:** 12 October 2026  
**Category:** Networking / IT Support / Wireless Troubleshooting  
**Outcome:** Resolved — CCTV remote viewing restored  
**Environment:** Residential building (anonymised)

## Situation

I helped a resident whose CCTV system stopped showing live video in the Hik-Connect mobile app after the broadband provider replaced the building's router. The app listed the recorder and all eight camera channels as offline. The installer had completed the broadband router change, but the legacy CCTV network connection was no longer working.

This was an external support experience, not part of my personal Proxmox homelab.

## Equipment involved

- EE broadband router / Smart Hub (new router)
- TP-Link TL-WR841N(EU), hardware version 14, 2.4 GHz Wireless N router
- Hikvision CCTV DVR/NVR and Hik-Connect mobile app
- Windows computer, browser and Command Prompt
- iPhone for testing the router management page

## Suspected network layout

Based on the cabling and successful recovery, the TP-Link was **likely configured as a wireless client/bridge or range extender with an Ethernet connection** to the Hikvision recorder. Its precise operating mode was not independently inspected.

```text
Internet
   |
New EE Smart Hub
   |
   | 2.4 GHz Wi-Fi (legacy-compatible network)
   |
TP-Link TL-WR841N
   |
   | Ethernet cable
   |
Hikvision DVR/NVR
   |
   +-- CCTV channels displayed through Hik-Connect
```

## Symptoms and evidence

1. The Hik-Connect app showed the recorder as `Device Offline` and all eight displayed camera channels offline.
2. The TP-Link had a single Ethernet cable connected to the CCTV recorder, with no second Ethernet uplink observed.
3. The replacement router was distributing a different Wi-Fi network name from the previous EE router.
4. The TP-Link was not identified in the new router's connected-device list during initial checks.
5. The new EE router's administration interface sometimes loaded incompletely, and Windows browser access was unreliable, while ordinary internet sites remained accessible.
6. Windows ICMP testing to the local default gateway showed intermittent failures during troubleshooting. These observations did not prove that general Wi-Fi packet loss caused the CCTV outage.

## Troubleshooting performed

### 1. Physical connectivity and device identification

I checked the equipment and identified the legacy TP-Link model and the Hikvision recorder. The cabling suggested that the TP-Link supplied an Ethernet connection to the recorder over a wireless uplink.

### 2. Check the replacement router

I inspected the local client IP configuration and default gateway using Windows `ipconfig` and iOS Wi-Fi network details. The router's administration interface was accessed from the local network and the device list reviewed.

Example diagnostic commands used:

```cmd
ipconfig
ping <router-lan-ip> -n 20
```

No real network identifiers are reproduced here.

### 3. Investigate wireless compatibility

The new router's primary network was enabled and used a WPA3 transition security mode. The older TP-Link supports 2.4 GHz Wi-Fi and was suspected of retaining the previous network's credentials.

The new EE router offered a separate **Compatible WiFi** feature intended for older devices, allowing the main Wi-Fi network to remain unchanged.

### 4. Apply the least disruptive fix

In the new router's **Advanced Wireless → Compatible WiFi** settings, I:

1. Enabled the compatible wireless network.
2. Set its SSID to match the previous router's SSID.
3. Set the password to match the previous router's Wi-Fi password.
4. Selected WPA2-Personal.
5. Enabled the 2.4 GHz radio.
6. Saved the configuration.
7. Power-cycled **only the TP-Link**, leaving the main router and Hikvision recorder settings intact.

The old SSID and password are deliberately excluded from this public write-up.

### 5. Validate service

After the TP-Link restarted, its previously amber status indicator changed to green. More importantly, the resident confirmed that the Hik-Connect CCTV system was working again.

The LED change was a useful clue, but the successful viewing test was the functional confirmation.

## Root cause assessment

**Most likely cause:** the TP-Link was still expecting the wireless SSID/security credentials of the former router. Replacing the broadband router had broken its wireless uplink and, consequently, the recorder's remote connectivity.

**Confidence:** high for the overall Wi-Fi configuration mismatch, supported by the restoration after recreating the old credentials. The TP-Link's exact wireless mode and the recorder's internal addressing were not directly verified.

## Resolution and impact

- Restored CCTV access for the resident.
- Avoided replacing any network or CCTV hardware.
- Preserved the primary Wi-Fi network and the Hikvision camera configuration.
- Avoided unnecessary factory resets.
- Demonstrated a practical low-risk troubleshooting workflow with a confirmed user outcome.

## Technical lessons learned

- **Map dependencies before changing equipment:** an internet router replacement can break downstream devices that depend on a particular SSID or authentication method.
- **Separate symptoms from root causes:** all cameras offline together can indicate a common recorder/uplink issue rather than eight independent camera failures.
- **Understand wireless limitations:** a 2.4 GHz Wireless N device may need a WPA2-compatible network even when the replacement router supports newer modes.
- **Use evidence to guide action:** check cabling, router client lists, local addressing, browser behavior and status indicators before modifying settings.
- **Prefer reversible, minimal changes:** adding a compatible SSID and restarting the wireless bridge was less disruptive than resetting the CCTV recorder.
- **Verify with the user:** a green LED is not enough; successful CCTV access is the meaningful end-to-end test.
- **Protect privacy:** never publish real Wi-Fi credentials, client MAC addresses, camera screenshots or a resident's identifying details.

## Skills demonstrated

- Network topology inference
- Wi-Fi SSID and WPA2/WPA3 compatibility
- Layer 1/2/3 troubleshooting
- DHCP and default-gateway inspection
- Windows network diagnostics
- Router web administration
- Legacy device support
- Customer assistance and incident documentation

---

*This is a retrospective of an actual support session. It documents observed evidence, decisions and verified outcome without inventing access to logs or device configuration that was not available.*
