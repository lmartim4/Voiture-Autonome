# VNC Setup

In order to have full access to the raspi environment you should now download a VNC sofware like [this one](https://www.realvnc.com/fr/connect/download/viewer/) from RealVNC.

Once you open the program just fill it up with the raspi informations:

- IP Address
- username
- password

![](/docs/images/vnc_setup/step1.png)
![](/docs/images/vnc_setup/step2.png)

If both raspi and your computer are connected to the same network and you did follow the [installation script](/docs/A_INSTALATION.md) *("Interface Options" -> "VNC" -> Hit Yes)* you should now see a screen like this:

You should see a screen like this:

![](/docs/images/vnc_setup/step3.png)

> Click on the terminal shortcut to open the terminal

![](/docs/images/vnc_setup/step4.png)

If everything worked well so far you should now be able to a terminal very much like the following.

![](/docs/images/vnc_setup/step5.png)

The installation script has made some changes to the system. One of them is this welcome message. It is triggered by a line added to **~/.bashrc** file. Actualy it calls the **.bash_quick_startup.sh** that helps us by:

* Setting up a useful command history
    - If you use arrow up you will should be able to quickly access the most used commands such as **python main.py**

### TIPS:

If the terminal looks small click and it and then use:

> "Ctrl" + "Shift" + "+"

The *control shift plus* shortcut will make the terminal bigger. You might use it multiple times until you fell confortable.

I found it useful to costumize the background appearence in order to make it clear to know in which Voiture I am. 

![](/docs/images/vnc_setup/step6.png)


```
Layout -> Centre image on screen
Picture -> raspberry-pi-logo.png
Colour -> Voiture's Color
Text -> One that fits well with the main background color
```
![](/docs/images/vnc_setup/step7.png)

If you followed everything up to this point you should have a system that looks like this:

![](/docs/images/vnc_setup/step8.png)


Now you can perform some tests yourself:

- Check if the lidar is working properly:
    - Use arrow up until you hit **python interface_lidar.py**

- Do the same for the other interfaces. Just be carefull because the motor interface might that the car to high speeds.

# Quick Debug

In a daily basis its easier to debug the car by testing each interface separately. Run at least the lidar and the camera before testing the **main.py**
