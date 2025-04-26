# First Boot

If you have followed [this](/docs/A_IMAGE_CREATOR.md) you should have a working raspi-os image on your SD card with a proper wifi config.

- Insert the SD card into the Raspi
- _Power on_ and hit the _reset button_ on the side

You will need to wait for it to boot (around one minute) and connect to your wifi's hotspot. You will then need to find its IP Address.

If all goes well you will probably find a table like this


| Hostname | IP |
| -------- | --- |
| Alice-PC      | 172.20.10.107 |
| Bob's Iphone  | 172.20.10.120 | 
| **Voiture-Jaune** | **172.20.10.3**   | 
| Bob-PC | 172.20.10.18 | 


> Note that the **voiture's IP might change** accordingly to the smartphone that is hosting the network.

# First connection

Once you have found the raspi's IP make sure the computer you are using to connect to the raspi is also connected to the same hotspot.

We are now going to connect to the raspi using SSH. Windows 10/11, Ubuntu, etc might already have it built-in installed.

run in terminal:

```
ssh ensta@the-ip-you-found

> example: ssh ensta@172.20.10.3
```

* Accept the figerprint, if asked
* Type in the password, it should be **ensta**

Once you are logged you should enable the VNC function that will allow us to connect to the raspi as a regular remote desktop, with graphics. For this run:

```
sudo raspi-config
```

Navigate to "Interface Options" -> "VNC" -> Hit Yes

![](/docs/images/raspi_config/step1.png)
![](/docs/images/raspi_config/step2.png)
![](/docs/images/raspi_config/step3.png)

Then quit this raspi-config menu.

You should receive a message like:

```
Created symlink /etc/systemd/system/multi-user.target.wants/wayvnc.service → /lib/systemd/system/wayvnc.service.
```

# Installation

To download the Voiture Software and automaticaly setup the raspi environment such as: 

- PWM config
- Lidar and Arduino Symbolic Links
- Python virtual envoronment
- Quick terminal access to code

You should follow the following commands step by step.

```
git clone https://github.com/lmartim4/Voiture-Autonome.git ~/Voiture-Autonome
~/Voiture-Autonome/install.sh
```

I hope you received a message like:

```bash
=== Installation Summary ===
SUCCESS: Autonomous-Vehicle project installation completed successfully!
INFO: Restart the system to apply all configurations: sudo reboot
```

Then all you should do is:

```
sudo reboot
```

> You should now wait for it to reboot and log back in via ssh just like you did previously.

If you receive a welcome message like this:

```
=============================================
        Welcome to Voiture-Jaune!
=============================================
Current Date: Fri Apr 25 21:17:36 CEST 2025
User:         ensta
Project Dir:  ~/Voiture-Autonome/code
--------------------------------------------
NOTE: You are now in a Python virtual environment
      Type deactivate to exit the environment
=============================================
```

It means that the installation is probably working fine!

You must test the VNC now. Please refer to [this](/docs/A_VNC.md) file