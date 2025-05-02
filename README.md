# esp32-mpy-pwm-fan-controller
MQTT-Enabled PWM Fan Controller with Thermistors and MicroPython on ESP32 

# Background
The purpose of this repository is to document, share, and hopefully polish over time an ESP32-based MicroPython PWM fan controller using thermistors. I created this project to monitor the temperatures of up to six hard drives in my DIY NAS.

In most PCs, fans are controlled based on CPU or GPU temperatures, but that’s not ideal for managing HDD temperatures. In my NAS, the drives usually idle cool, but during operations like scrubs or backups—where several terabytes of data are read continuously—they start heating up. That’s where this controller comes in: it monitors HDD temps and ramps up dedicated fans as needed to keep them in a safe range.

The system publishes fan duty, RPM, and temperature readings over MQTT, allowing integration with platforms like Home Assistant for monitoring and automation.

# Status 
🚧 Work in progress – the project is currently being populated...
