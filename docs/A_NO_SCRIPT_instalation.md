# Booting on RPi 5

> 2025 - [RASPI 19-11-2024](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64.img.xz)
> 2024 - [RASPI 05-12-2023](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2023-12-06/2023-12-05-raspios-bookworm-arm64.img.xz)

## PWM Configuration

Execute the following commands:

```
sudo nano /boot/firmware/config.txt
```

Append the following line to the file 

```
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

## Create the alias

Execute the following commands to create the symbolic link to both Arduino and Lidar

```
sudo touch /etc/udev/rules.d/99-devices.rules
sudo nano /etc/udev/rules.d/99-devices.rules
```

Add the following lines

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8057", SYMLINK+="ttyACM"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyUSB"
```

Now you should clone the repository

```
sudo apt-get update
sudo apt-get install -y python3-tk python3-pil.imagetk

git clone https://github.com/lmartim4/Voiture-Autonome.git ~/Voiture-Autonome

cd ~/Voiture-Autonome/code
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

You would need to open terminal and always run the following commands:

```
cd ~/Voiture-Autonome/code
source venv/bin/activate
python main.py
```

To avoid this you might want to use the Quick StartUp Bash Script. To install it you need to save **scripts/.bash_quick_startup.sh** in **~/.bash_quick_startup.sh** and then add the source command to **.bashrc** so it is always called when opening a terminal session.

```
cp ~/Voiture-Autonome/scripts/.bash_quick_startup.sh ~/.bash_quick_startup.sh
```

Add the following line to **.bashrc** 

```
source ~/.bash_quick_startup.sh
```