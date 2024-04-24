# Voiture Autonome

![Raspberry Pi](https://img.shields.io/badge/-RaspberryPi-C51A4A?style=for-the-badge&logo=Raspberry-Pi)
![Arduino](https://img.shields.io/badge/-Arduino-00979D?style=for-the-badge&logo=Arduino&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)

# Table des matières

* [Introduction](#introduction)
* [Premiers pas](#premiers-pas)
  * [Clonage](#clonage)
  * [Installation](#installation)
  * [Configuration](#configuration)
* [Calibration des actionneurs](#calibration-des-actionneurs)
* [Test de communication avec l'Arduino](#test-de-communication-avec-larduino)
* [Exécution du code](#exécution-du-code)
  * [Fichiers associés](#fichiers-associés-2)
  * [Commande dans le terminal](#commande-dans-le-terminal-2)
* [Analyse du *log*](#analyse-du-log)
* [Détails de l'algorithme](#détails-de-lalgorithme)
  * [Architecture](#architecture)
  * [Mesure du lidar](#mesure-du-lidar)
  * [Loi de direction](#loi-de-direction)
  * [Loi de vitesse](#loi-de-vitesse)
  * [Interpolation linéaire](#interpolation-linéaire)
  * [Détection de la marche arrière](#détection-de-la-marche-arrière)
  * [Activation de la marche arrière](#activation-de-la-marche-arrière)
* [Boot sur RPi 5](#boot-sur-rpi-5)
  * [Configuration PWM](#configuration-pwm)
  * [Création d'un alias](#création-dun-alias)
* [Contact](#contact)

# Introduction

TODO

# Premiers pas

Pour prendre les premiers pas dans le projet, on doit d'abord télécharger le code et préparer tout l'environnement dans lequel on travaillera.

## Clonage

Appuyez sur `CTRL+ALT+T` pour ouvrir un terminal et exécutez les commandes ci-dessous (un par ligne) :

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
- Dans le fichier `main.py`, indiquez dans les lignes 38 à 41 les paramètres du matériel utilisé, le *baudrate*, etc.
- Dans le fichier `constants.py`, indiquez à la ligne 10 l'orientation du LiDAR (angle dans le repère du LiDAR où se trouve l'avant du véhicule).

# Calibration des actionneurs

Les actionneurs du véhicule sont contrôlés par une technique appelée [PWM](https://learn.sparkfun.com/tutorials/pulse-width-modulation/all) (*Pulse Width Modulation*), où la position du servomoteur et la vitesse du moteur *brushless* dépendent du *duty cycle* appliqué. La calibration consiste précisément à trouver ces valeurs de *duty cycle* qui permettent à la direction de tourner au maximum dans les deux sens, ainsi que la valeur qui limitera la vitesse maximale du véhicule.

## Fichiers associés

📁 `calibrate.py` est le code responsable de la calibration des actionneurs du véhicule (servomoteur pour la direction et moteur *brushless* pour la traction). En exécutant ce code, on pourra contrôler manuellement chacun des actionneurs à partir d'une interface graphique de calibration et de test.

## Commande dans le terminal

```
python calibrate.py
```

Après avoir fermé l'interface graphique, le programme mettra à jour automatiquement le fichier `constants.py`.

# Test de communication avec l'Arduino

La connexion série entre le Raspberry Pi et l'Arduino Nano se fait à l'aide d'un câble USB vers mini USB. Cette même connexion peut être utilisée pour téléverser des programmes du RPi vers l'Arduino.

## Fichiers associés

📁 `arduino.py` est le code responsable de tester la communication série entre le RPi et l'Arduino. En exécutant ce code, on pourra visualiser les mesures des capteurs envoyées de manière sérielle par l'Arduino et reçues par le RPi.

## Commande dans le terminal

```
python arduino.py
```

Les valeurs reçues par la communication série avec l'Arduino seront affichées sous le format :

```
capteur_de_vitesse/distance_de_recul/tension_de_la_batterie
```

Les unités de chaque quantité sont respectivement `m/s`, `cm` et `volt`.

# Exécution du code

Maintenant que tout est correctement préparé, on attache les ceintures ! 🏁

## Fichiers associés

📁 `console.py` est le code responsable de gérer les messages imprimés dans le terminal et de créer et gérer les *logs* de chaque exécution du code principal. Ce code n'est pas exécuté directement, mais utilisé par `main.py`.

📁 `constants.py` est le code responsable de stocker toutes les constantes qui contrôlent le comportement du véhicule. Ce code n'est pas exécuté directement, mais utilisé par d'autres fichiers. Certaines valeurs sont modifiées automatiquement lorsque la calibration des actionneurs est réalisée, minimisant l'effort.

📁 `control.py` est le code responsable de définir les lois de contrôle du véhicule à partir des données sensorielles. On aura une session plus loin pour expliquer en détail les lois de direction et de vitesse. Ce code n'est pas exécuté directement, mais utilisé par `main.py`.

📁 `core.py` est le code responsable de définir certaines structures de base qui seront utiles dans d'autres parties du projet, telles qu'un contrôleur PWM et un gestionnaire de communication série. Ce code n'est pas exécuté directement, mais utilisé par d'autres fichiers.

📁 `main.py` est le code responsable de réaliser toute la routine d'initialisation des capteurs et actionneurs, le contrôle du véhicule pendant la course et la fermeture correcte de toutes les structures initialisées. Il unit les autres composants du projet. En exécutant ce code, le véhicule sera correctement initialisé, entrant dans une routine d'attente jusqu'à ce que le signal GO soit donné pour le début de la course.

## Commande dans le terminal

```
python main.py
```

Appuyez sur `ENTER` pour démarrer et sur `CTRL+C` pour arrêter le code. Deux touches sont utilisées pour éviter les arrêts accidentels du véhicule.

⚠️ **Important :** la commande exacte pour analyser le *log* généré après la fin de la course sera copiée dans le presse-papiers (*clipboard*).

# Analyse du *log*

IMAGE HERE

## Fichiers associés

📁 `multiplot.py` est le code responsable d'interpréter le fichier CSV du *log* et de tracer les graphiques de manière séparée, permettant l'analyse et l'obtention d'aperçus de la manière la plus rapide possible. En exécutant ce code, un écran matplotlib avec 5 graphiques sera affiché. Le graphique le plus à gauche représente la mesure du lidar pour l'instant de temps en question, tandis que les 4 autres graphiques montreront une fenêtre temporelle avec les mesures des métriques respectives (les grandeurs et unités sont correctement identifiées dans l'interface elle-même).

## Commande dans le terminal

Il suffit de coller la commande copiée dans le presse-papiers (*clipboard*).

```
python multiplot.py "../logs/YYYY-MM-DD/HH-MM-SS.csv"
```

Remarquez que `YYYY-MM-DD` représente l'année, le mois et le jour, tandis que `HH-MM-SS` représente l'heure, la minute et la seconde où le *log* a été généré. Il sera unique pour chaque course et garantit que les *logs* ne se chevauchent pas.

Pour modifier le moment dans le temps des graphiques, utilisez le *slider* en bas à gauche. Pour un contrôle plus précis, utilisez les flèches du clavier pour passer itération par itération. Appuyez sur la touche `CTRL` tout en utilisant les flèches du clavier pour augmenter la taille du pas.

# Détails de l'algorithme

TODO

## Architecture

TODO

## Mesure du lidar

La mesure du lidar se compose d'un vecteur de 360 positions de nombres flottants où l'indice représente l'angle en degrés dans le repère du lidar et la valeur allouée à cette position correspond à la distance respective en mètres. Par exemple, l'élément à la position 90 équivaut à la distance mesurée sur le côté gauche du lidar (pas nécessairement à gauche de la voiture). Notez que les angles sont mesurés dans le sens antihoraire.

Le module `rplidar` possède la fonction `iter_scans()` qui permet d'itérer sur les balayages du lidar. Il est à noter que chaque balayage contiendra les distances mesurées pour un petit intervalle angulaire, de sorte que nous devons regrouper plusieurs de ces balayages pour composer une mesure du lidar. Lorsque le vecteur de distances comporte plus de 60 points non nuls, il est alors considéré que la mesure est suffisante pour progresser dans le code.

⚠️ **Important :** comme le module `rplidar` utilise un générateur pour implémenter la fonction `iter_scans()`, le code de contrôle doit être suffisamment rapide pour ne pas générer d'accumulation de balayages et surcharger le *buffer*.

## Loi de direction

La première chose à faire est de filtrer le nuage de points du lidar et de séparer la région d'intérêt principale. La fonction `filter` sélectionnera uniquement les points qui se trouvent dans un certain champ de vision du véhicule. Ce champ de vision est calculé à partir de l'avant de la voiture et d'une ouverture donnée (la moitié de chaque côté). Ensuite, une convolution sera appliquée pour lisser et réduire les erreurs. On peut comprendre la convolution comme une moyenne entre les points voisins. Augmentez `CONVOLUTION_SIZE` pour augmenter cette voisinage et, par conséquent, le lissage effectué.

Maintenant que le nuage de points a été correctement traité, on trouvera l'angle associé au point le plus éloigné. De légères perturbations seront appliquées vers la droite et vers la gauche de cet angle afin de vérifier si la voiture atteindrait d'éventuels coins de la piste. Notez que pour vérifier la présence de coins, on utilise la mesure non filtrée, car le vecteur filtré aura les coins lissés.

Supposons qu'un coin a été trouvé à droite du véhicule, alors on déplacera l'angle de direction vers la gauche afin d'éviter de heurter l'obstacle. Dans ce cas, ce déplacement serait donné par :

```python
delta = -ANGLE_SCALE_FACTOR * (MAX_ANGLE_TO_AVOID_CORNER - r_angle)
```

Les constantes `ANGLE_SCALE_FACTOR` et `MAX_ANGLE_TO_AVOID_CORNER` contrôlent le facteur d'augmentation de ce déplacement et la taille de la perturbation angulaire.

Ainsi, on peut calculer l'angle de direction corrigé $\alpha$. Cependant, l'angle de braquage effectif des roues $\delta$ sera une fonction de $\alpha$. Cette fonction $f$ est définie dans `STEER_FACTOR` par une carte de points interpolés linéairement.

$$\delta(\alpha) = \text{sign}(\alpha) \cdot f(\,|\alpha|\,)$$

⚠️ **Important :** un angle de braquage positif indique que la voiture doit tourner à gauche, tandis qu'une valeur négative indique que la voiture doit tourner à droite.

## Loi de vitesse

Avec le braquage $\delta$ calculé, il est temps de passer à la vitesse. Un petit cône sera filtré dans la région frontale du véhicule afin de calculer sa distance frontale $d_f$. La vitesse $v$ sera une fonction de $d_f$ et de $\delta$ de la manière suivante :

$$v(d_f, \delta) = \kappa + (1-\kappa) \cdot g(d_f) \cdot h(\,|\delta|\,)$$

où $\kappa$ est une constante qui détermine l'agressivité de la direction. Plus proche de 1, moins la voiture freinera dans les virages, mais le risque de perdre le contrôle est également plus élevé. Les fonctions $g$ et $h$ sont définies respectivement dans `SPEED_FACTOR_DIST` et `SPEED_FACTOR_ANG` à l'aide de cartes de points interpolés linéairement.

Remarquez que la fonction $h$ vise à accélérer dans les lignes droites (petit braquage) et à freiner encore plus dans les virages, augmentant la réactivité du véhicule.

## Interpolation linéaire

TODO

## Détection de la marche arrière

TODO

## Activation de la marche arrière

TODO

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

# Contact

En cas de doutes, n'hésitez pas à envoyer un message !

> Filipe **LACERDA**
>
> filipe.lacerda@ensta-paris.fr
>
> +33 7 82 74 86 81
