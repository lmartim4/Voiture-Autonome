# WiFi Hotspot

> Do not connect the raspi to multiple networks. Keep it simple. Just one WiFi (SSID, password). **Do not try eduroam or any other public network.**

> Use the exact same WiFi credentials to host networks in differents smartphones. But only host one hotspot at a time.

## Goal

We want to access/manipulate the raspi system through a laptop in such a way that we don't need extra hardware (keyboard, mouse, monitor).

You will need:

- Smartphone or Router.
- Laptop
- Raspberry Pi

## Getting Started

### Create the Voiture's hotspot

In the most commom scenario you will have an Android phone. You should go to the **hotspot configuration menu** and set up a network with the following parameters:

```
SSID: PIE_ENSTA
Password: Voiture-ENSTA

2.4 Ghz only (optional, it maximizes compatibility)
```

### Find Voiture's IP

You will need to power up the raspi then wait for it to boot (around one minute) and connect to your wifi's hotspot. You will then need to find its IP Address.

If all goes well you will probably find a table like this in your phone's hotspot section:

| Hostname          | IP            |
| --------          | ---           |
| Alice-PC          | 172.20.10.107 |
| Bob's Iphone      | 172.20.10.120 | 
| **Voiture-Jaune** |**172.20.10.3**| 
| Bob-PC            | 172.20.10.180 | 

If it doesn't connect to your phone you might need to plug in a monitor to discover what is going on.

* Check if you correctly spelled the **SSID** and **password** in your phone.
* Make sure the raspi is on. 
    - If you are with the Raspberry Pi 5 you need to press the reset button on the side if the led is in RED. It must be blinking/static green to mean that the system properly booting working.
    - An unchaarged battery might lead the system to constantly power off / loop reseting.
* Plug in just a HDMI monitor to check if the system is booting to Desktop.
    - Plug in a keyboard and mouse and navigate to the Wi-Fi parameters on the raspi to make sure it is trying to connect to the same network.
* If nothing works and you wish to completlely reset the system to "factory mode", refer to [image creating guide](/docs/A_IMAGE_CREATOR.md). Note that this is usually an extreme solution.

#### iPhone Warning:
In case you have an **iPhone** you will need to **change your phones name** to the choosen SSID. In order to find the voiture's ip address you will then need an app like **Net Analyzer** to scan your new network and check if the raspi has connected and if so, which ip address it has. I used **iPhone** most of the time, it was verry commom for the iPhone to simply stop accepting new connections. Sometimes it was hard to debug and discover why things stopped working. Android seemed to always work just fine.

### Connect your laptop to the same Hosspot

Both Raspi and Laptop should be on the same network for VNC/SSH to work. This is simple, but sometimes your laptop might reconnect to other Wi-Fi such as **eduroam**. When it happens we usually take some time to notice. I recommend you to **disable auto-connect to other networks**, this will certainly save your time.


Once you can see at your phone that both laptop and raspi are connected. Refer to [VNC Guide](/docs/A_VNC.md) on how to connect via VNC and later [VSCode Guide](/docs/A_VSCODE_Setup.md) on how to connect via VSCode (SSH).