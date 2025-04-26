# How are components connected?

The Voiture-Autonome has the following main components:

* Raspeberry Pi 5
* Arduino
* Lidar
* ESC (Eletronic Speed Controller)
* Servo Motor (Steering motor)
* Traction Motor
* Ultrassonic Sensor (in the back)
* Encoder attached to car's wheel
* Voltage Sensor

To understand how the car works is crucial to understand what are the components above, how they work and how do they interact.

Lets start from bottom to top.

## Arduino conneted components

This section constains the 3 devices that are directly connected to the arduino. It is important to know the flux of information.

### Voltage Sensor

It consists of on **Analog Digital Converter** (ADC) that will convert a voltage to a logical singal. It is used to estimate how much bettery we still have. The current batteries are fully charged around 8.2 V and very lo when reaching to 7.0 V.

It is conncted directly to the **Arduino**.

### Wheel Encoder

An encoder is a device that will trigger a rising/falling logic signal in a cable that allows us to detect movement. There is [this video](https://www.youtube.com/watch?v=oLBYHbLO8W0&ab_channel=SparkFunElectronics) that teaches how it works, I really recomend you to watch it.

> In the [Arduino docs](/docs//A_Arduino.md) we will better explore its functioning.

At the moment we only use it to measure the linear speed of the Voiture.

It is conncted directly to the **Arduino**.

### Ultrassonic Sensor

It is a device that will try to estimate the distance from itself to the closest object in its frontal side. This kinda of component is not so reliable. It is not really accurate and is indeed very susceptible to failures.

It is conncted directly to the **Arduino**.


## Traction Motor

It is the component that consumes the most of the car's battery. Each Voiture has one. It is controlled by the ESC by applying a specific voltage to its poles.

It is conncted directly to the **ESC**.

## Servo Motor

It is a component that has a closed control system. It is used to control the cars direction. It works by applying an specific **duty cicle PWM signal** to its control pin. You might want to watch [this video](https://www.youtube.com/watch?v=1WnGv-DPexc&ab_channel=TheEngineeringMindset) to learn more.


Its control pin conncted directly to the **Raspberry Pi**.

## ESC (Eletronic Speed Controller)

It is a component that is connected beetwen the battery and the motor. It works like a power regulator that is controlled the same way as the servo. A PWM duty-cycle will tell the esc with we want to go forward/backwards/break and at which intensity.

Not all ESCs works the same way, therefore are not controlled the same way. However both cars have similar ESCs, due to this the **interface_motor.py** should work fine, already encapsulating this logic of configuring the ESC mode, etc. If you look up at this file you will notice that the logic to set it to backwards mode is not so trivial.

Its control pin conncted directly to the **Raspberry Pi**.

## Lidar

It is essential for the Voiture, functioning as its primary spatial sensing system. It operates by emitting laser pulses that reflect off surrounding objects, measuring return times to calculate precise distances and creating detailed 2D environmental maps. This enables the Voiture to accurately detect walls and obstacles in real-time across various lighting conditions, providing the critical spatial awareness necessary for navigation and decision-making in runtime.

It is connected to a **UART to USB Serial Port Adapter Board** that is connected to both **Raspberry Pi** and Voiture's **battery**. This UART converter has 2 modes (baudrate). Jaune's lidar works at 256000 and Bleu's at 115200. 

It is crucial to set it up at the logical switch in this **UART to USB Serial Port Adapter Board**. It is a switch on the lateral.

## Raspeberry Pi 5

This is the brain of the Voiture. It receives all lidar readings and Arduino readings, transforming it in control signals to both ESC and Servo Motor.

It runs Raspi OS + Voiture-Autnome python algorithm.

More on how the Voiture Software/Algorithm works [here](/docs/A_Voiture_Software.md) 