# Boot sur RPi 5

Utilisez le [`2023-12-05-raspios-bookworm-arm64.img.tar.xz`](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2023-12-06/2023-12-05-raspios-bookworm-arm64.img.xz) pour démarrer le RPi 5.

⚠️ **Important :** le noyau utilisé doit être le 6.1 et il ne faut pas effectuer de mises à jour, car le noyau 6.6 présentait certains problèmes au moment du développement (mars 2024).

## Configuration PWM

Exécutez la commande ci-dessous pour éditer le fichier en question :

```
sudo nano /boot/firmware/config.txt
```

À la fin du fichier, ajoutez les lignes suivantes :

```
# Enable PWM
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Appuyez sur `CTRL+O` pour enregistrer et `CTRL+X` pour quitter l'éditeur de texte. Redémarrez le RPi.

## Création d'un alias

Exécutez les commandes ci-dessous pour créer et éditer un fichier de règles :

```
sudo touch /etc/udev/rules.d/99-devices.rules
sudo nano /etc/udev/rules.d/99-devices.rules
```

Ajoutez les lignes suivantes :

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8057", SYMLINK+="ttyACM"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyUSB"
```

Appuyez sur `CTRL+O` pour enregistrer et `CTRL+X` pour quitter l'éditeur de texte. Redémarrez le RPi ou débranchez et rebranchez les périphériques.

Les valeurs `idVendor` et `idProduct` peuvent être trouvées en exécutant la commande `dmesg`, mais il y a une forte probabilité qu'elles soient les mêmes que celles de la commande ci-dessus.

Ainsi, il n'est pas nécessaire de spécifier si le LiDAR est connecté au port `ttyUSB0` ou `ttyUSB1`, par exemple, évitant les erreurs où le port change pendant l'exécution du code.

## Quick Start-Up trick

You must install picamera2