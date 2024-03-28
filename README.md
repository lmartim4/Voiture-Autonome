# Voiture Autonome

![Raspberry Pi](https://img.shields.io/badge/-RaspberryPi-C51A4A?style=for-the-badge&logo=Raspberry-Pi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)

## Clonage

Appuyez sur `CTRL+ALT+T` pour ouvrir un terminal et exécutez les commandes ci-dessous :

```
cd Desktop
git clone https://github.com/l4cer/Voiture-Autonome.git
cd Voiture-Autonome/code_24
```

## Installation

Créez un environnement virtuel et installez les modules nécessaires :

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

⚠️ **Important :** pour toutes les sections ci-dessous, exécutez les commandes à l'intérieur du dossier `code_24` et avec l'environnement virtuel activé !

## Configuration

- Dans le fichier `core.py`, indiquez à la ligne 10 si le RPi utilisé est le 5 ou non.
- Dans le fichier `main.py`, indiquez dans les lignes 38 à 41 les paramètres du matériel utilisé, le *baudrate*, le canal, etc.
- Dans le fichier `constants.py`, indiquez à la ligne 10 l'orientation du LiDAR (angle dans le repère du LiDAR où se trouve l'avant du véhicule).

## Calibration des actionneurs

```
python calibrate.py
```

Après avoir fermé l'interface graphique, le programme mettra à jour automatiquement le fichier `constants.py`.

## Test de communication avec l'Arduino

```
python arduino.py
```

Les valeurs reçues par la communication série avec l'Arduino seront affichées sous le format :

```
capteur de vitesse / distance de recul / tension de la batterie
```

## Exécution du code

```
python main.py
```

Appuyez sur `ENTER` pour démarrer et sur `CTRL+C` pour arrêter le code.

⚠️ **Important :** la commande exacte pour analyser le *log* généré après la fin de la course sera copiée dans le presse-papiers (*clipboard*).

## Analyse du *log*

Il suffit de coller la commande copiée dans le presse-papiers (*clipboard*).

```
python multiplot.py "../logs/YYYY-MM-DD/HH-MM-SS.csv"
```

Remarquez que `YYYY-MM-DD` représente l'année, le mois et le jour, tandis que `HH-MM-SS` représente l'heure, la minute et la seconde où le *log* a été généré. Il sera unique pour chaque exécution et garantit que les *logs* ne se chevauchent pas.

Pour modifier le moment dans le temps des graphiques, utilisez le *slider* en bas à gauche. Pour un contrôle plus précis, utilisez les flèches du clavier pour passer itération par itération. Appuyez sur la touche `CTRL` tout en utilisant les flèches du clavier pour augmenter la taille du pas.

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