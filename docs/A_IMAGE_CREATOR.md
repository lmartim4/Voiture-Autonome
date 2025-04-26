# How to configure the RASPI OS from scratch

## Local WiFi setup

In order to access the raspberry system you will need a wifi hotspot.
We usually use a smartphone (Android is better in this case) to host a local network that will allow us to work.

> Do not connect the raspi to eduroam, eduspot or any public WiFi. Create your own so we can always be sure to which network its connected.

Suggestion:
```
SSID: PIE_ENSTA
Password: Voiture-ENSTA
```

> If you are *struggling* or want a more detailled tutorial refer to the [Wi-Fi Setup guide](/docs/A_WIFI_SETUP.md)

## Creating the RaspiOS Image

Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)

Pick the last stable version available or one of the following. Both versions were used in the previous competitions

> 2025 - [RASPI 19-11-2024](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64.img.xz)  
> 2024 - [RASPI 05-12-2023](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2023-12-06/2023-12-05-raspios-bookworm-arm64.img.xz)



![Raspberry Pi Imager First Screen](/docs/images/imager/RASPI_IMAGER.png)


![First Config Details](/docs/images/imager/config1.png)

Make sure you put the right color in the hostname. It will be easier to debug in which raspi we are connected when both are online.

```
Hostname: Voiture-Color
Username: ensta
Password: ensta
SSID: PIE_ENSTA
Password: Voiture-ENSTA
Wireless LAN Country: FR
```

![Second Config Details](/docs/images/imager/config2.png)

When finished export the card. Insert into Raspi and follow [Instalation Guide](/docs/A_INSTALATION.md)