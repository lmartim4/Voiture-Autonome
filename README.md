# Voiture Autonome

![Raspberry Pi](https://img.shields.io/badge/-RaspberryPi-C51A4A?style=for-the-badge&logo=Raspberry-Pi)
![Arduino](https://img.shields.io/badge/-Arduino-00979D?style=for-the-badge&logo=Arduino&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-27338e?style=for-the-badge&logo=OpenCV&logoColor=white)

This project has a guide-like documentation: The goal it to teach you from getting a brand new raspi with no operating system up to connecting to it via vscode and performing usefull tests.

## Getting started with a pre-configured voiture

If someone has already setup the raspi and installed the Voiture software (which is usually the case) you will only need the following to get started:

- WiFi hotspot
- VNC
- VSCode

Here comes a quick guide on how to solve these 3 points:


### WiFi hostspot



Both cars are configured to connect to a WiFi hotspot with these credentials:

```
SSID: PIE_ENSTA
Password: Voiture-ENSTA
```

Use you mobile to host a local network with those parameters and you should be fine. If you have an **Android phone** it should work better. If it is connected to a network that has internet access such as **eduroam** the hotspot you create will probably share this internet connection to the car, which does not seem to occcur when sharing iphones internet. In an environment where 4G/5G doesn't work (like at ENS) it is great to have an Android phone to allow us to share eduroam access to the Voiture.

> Do not try to configure the raspi to multiple networks. Sometimes you might struggle to know to which phone the car connected. Much worse happens when trying to use public networks like eduroam, eduspot, etc

> If you are *struggling* or want a more detailled tutorial refer to the [Wi-Fi Setup guide](/docs/A_WIFI_SETUP.md)

### VNC

To access / control the Raspberry Pi as a remote desktop, please refer to the [VNC Setup](/docs/A_VNC.md)

### VSCode

To navigate through the files and code the Voiture Sofware, I recommend you to use VSCode's remote tunnel so you can quickly get started with the actual coding. Follow the [VSCode SSH Setup](/docs/A_VSCODE_Setup.md)

## Configuring a new Raspi from scratch

In case the system is corrupted or for any reason you do not have a working system configured on the SD Card please follow this 4 step tutorial:

1. [Image Creation](/docs/A_IMAGE_CREATOR.md)
1. [Software Installation](/docs/A_INSTALATION.md)
1. [VNC Setup](/docs/A_VNC.md)
1. [VSCode SSH Setup](/docs/A_VSCODE_Setup.md)