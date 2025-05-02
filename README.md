# esp32-mpy-pwm-fan-controller
MQTT-Enabled PWM Fan Controller with Thermistors and MicroPython on ESP32

# Status 
🚧 Work in progress – the project is currently being populated...

# Background
The purpose of this repository is to document, share, and hopefully polish over time an ESP32-based MicroPython PWM fan controller using thermistors. I created this project to monitor the temperatures of up to six hard drives in my DIY NAS.

In most PCs, fans are controlled based on CPU or GPU temperatures, but that’s not ideal for managing HDD temperatures. In my NAS, the drives usually idle cool, but during operations like scrubs or backups—where several terabytes of data are read continuously—they start heating up. That’s where this controller comes in: it monitors HDD temps and ramps up dedicated fans as needed to keep them in a safe range.

The system publishes fan duty, RPM, and temperature readings over MQTT, allowing integration with platforms like Home Assistant for monitoring and automation.

# Schematics
[Fritzing schematic file](schematics/schematics.fzz)

[<img src="images/schematics.png" width="200"/>](images/schematics.png)

# Parts list
*1× ESP32 controller
*1× 12V PWM fan (additional fans can be chained if they have compatible connectors)
*6× 10kΩ NTC thermistor temperature sensors
*7× 10kΩ resistors
*1× 2kΩ resistor
*1× 1kΩ resistor
*1× 0.1 nF ceramic capacitor
*1× 4-pin male fan connector
*1× 4-pin male power supply connector (3-pin could also be used)
*2× 18×24 hole prototyping PCB boards
*1× SATA to Molex power adapter (Molex connector removed and wired directly to PCB power input)
*24 AWG wire
