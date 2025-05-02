# region import libraries
import gc
import network
import uasyncio
import ujson
import math
from umqtt.simple import MQTTClient # Make sure to install umqtt.simple external library
from utime import sleep
from machine import ADC, Pin, PWM
import secrets
# endregion

# region constants
BETA = 3950  # Beta value for thermistor
R_REF = 10000  # Reference resistor value
V_SUPPLY = 5.0  # Supply voltage (5V for ESP32)
DELTA_C = 0 # Temperature measurement correction
THERMISTOR_PINS = [32, 33, 34, 35, 36, 39]  # List of thermistor ADC pins
SETTINGS = {    # PWM Duty depending on max temperature
    0:  20,
    10: 30,
    20: 38,
    30: 40,
    40: 42,
    50: 44,
    60: 46,
    70: 48,
    80: 50,
    90: 51,
    100: 52
}
# endregion

# Global variables
fan = PWM(Pin(5))  # Fan PWM control
thermistor_temps = {}  # To store temperatures for each pin
temp_C_max = 40  # Initial max temperature
duty = 10  # Initial duty cycle
RPM_PIN = 23  # Change if using a different GPIO pin
pulse_count = 0 # Initial pulse count 
rpm = 0 # Initial rpm count


# Initialize thermistors
thermistors = [ADC(Pin(pin, Pin.IN)) for pin in THERMISTOR_PINS]
for t in thermistors:
    t.atten(ADC.ATTN_11DB)  # Set attenuation for full range (0-3.3V)
# Initialize fan
fan.duty(duty * 1023 // 100)  # Initial duty cycle
# Initialize pin with pull-up resistor manually
rpm_sensor = Pin(RPM_PIN, Pin.IN, pull=Pin.PULL_UP)





# region fan control
def set_duty(temp):
    global duty, SETTINGS
    if temp < SETTINGS[0]:
        duty = 0
    elif temp > SETTINGS[100]:
        duty = 100
    else:
        items = sorted(SETTINGS.items(), key=lambda item: item[1])
        for i in range(len(items) - 1):
            duty_low, temp_low = items[i]
            duty_upp, temp_upp = items[i + 1]
            if temp_low <= temp <= temp_upp:
                duty = round(duty_low + (temp - temp_low) * (duty_upp - duty_low) / (temp_upp - temp_low))
    
    fan.duty(duty * 1023 // 100)
    print(f">>> Max temp: {temp}C, setting duty to: {duty}%")
def fan_control():
    set_duty(temp_C_max)
    gc.collect()
# endregion


# region read settings
def read_fan_settings(filename="/settings.cfg"): # try read settings from settings.cfg
    global SETTINGS
    try:
        with open(filename, "r") as f:
            new_settings = {}
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):  
                    try:
                        pwm, temp = line.split("=")
                        new_settings[int(pwm)] = int(temp)
                    except ValueError:
                        print(f"Skipping invalid line: {line}")
            if new_settings:
                SETTINGS = dict(sorted(new_settings.items()))
            else:
                print("Invalid file format. Using defaults.")
    except OSError:
        print("Error: settings.cfg not found. Using defaults.")
    
    gc.collect()
# endregion


# region thermistor readings
async def read_temps():
    global temp_C_max
    while True:
        temperatures = []
        for i, thermistor in enumerate(thermistors):
            pin = THERMISTOR_PINS[i]
            voltage = thermistor.read_uv() / 1_000_000
            resistance = R_REF * voltage / (V_SUPPLY - voltage) if voltage > 0 else float("inf")
            try:
                temp_K = 1 / ((math.log(resistance / R_REF) / BETA) + (1 / (273.15 + 25)))
                temp_C = temp_K - 273.15 + DELTA_C
            except ValueError:
                temp_C = 40 # If math fails assume temp 40C
            
            thermistor_temps[pin] = int(temp_C)
            temperatures.append(temp_C)

        print(thermistor_temps)
        temp_C_max = max((t for t in thermistor_temps.values() if t is not None), default=40)
        
        fan_control()
        await uasyncio.sleep(1)  # Sleep to yield control
# endregion


# region wifi connect
async def wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    while True:    
        if not sta_if.isconnected():
            print('Connecting to network...')
            sta_if.active(False)
            await uasyncio.sleep(60)
            sta_if.active(True)
            sta_if.connect(secrets.WIFI_SSID, secrets.WIFI_PWD)
            
        if sta_if.isconnected():
            print('Network config:', sta_if.ifconfig())
        
        await uasyncio.sleep(60)
# endregion

# region mqtt publish

async def mqtt_publish():
    sta_if = network.WLAN(network.STA_IF)
    global duty, rpm
        
    # Wait for WiFi connection
    while not sta_if.isconnected():
        print("Waiting for WiFi...")
        await uasyncio.sleep(30)

    mqtt_client = MQTTClient("esp32_client", secrets.MQTT_SRV, user=secrets.MQTT_USR, password=secrets.MQTT_PWD)
    try:
        mqtt_client.connect()
        print("Connected to MQTT broker")
        
        while True:
            if sta_if.isconnected():
                # Publish fan frequency, rpm
                discovery_topic = f"homeassistant/sensor/tnas_fan_rpm/config"
                discovery_payload = {
                    "name": f"Truenas tnas_fan_rpm sensor",
                    "state_topic": f"homeassistant/sensor/tnas_fan_rpm/freq",
                    "unit_of_measurement": "rpm",
                    "device_class": "frequency",
                    "unique_id": f"tnas_fan_rpm",
                    "expire_after": 60
                }
                discovery_message = ujson.dumps(discovery_payload)
                mqtt_client.publish(discovery_topic, discovery_message)
                mqtt_client.publish(f"homeassistant/sensor/tnas_fan_rpm/freq", str(int(rpm)))
                print(f"Published tnas_fan_rpm temp: {int(rpm)} rpm")
                await uasyncio.sleep(0.1)


                # Publish initial availability status
                mqtt_client.publish(f"homeassistant/sensor/tnas_fan_duty/availability", "online")
                # Publish fan pwm duty, %
                discovery_topic = f"homeassistant/sensor/tnas_fan_duty/config"
                discovery_payload = {
                    "name": f"Truenas tnas_fan_duty sensor",
                    "state_topic": f"homeassistant/sensor/tnas_fan_duty/pwr",
                    "unit_of_measurement": "%",
                    "device_class": "power",
                    "unique_id": f"tnas_fan_duty",
                    "expire_after": 60
                }
                discovery_message = ujson.dumps(discovery_payload)
                mqtt_client.publish(discovery_topic, discovery_message)
                mqtt_client.publish(f"homeassistant/sensor/tnas_fan_duty/pwr", str(duty))
                print(f"Published tnas_fan_duty: {duty}%")
                await uasyncio.sleep(0.1)

                # Publish thermistor data
                for key, temp in thermistor_temps.items():
                    discovery_topic = f"homeassistant/sensor/tnas_pin{key}/config"
                    discovery_payload = {
                        "name": f"Truenas pin{key} sensor",
                        "state_topic": f"homeassistant/sensor/tnas_pin{key}/temp",
                        "unit_of_measurement": "C",
                        "device_class": "temperature",
                        "unique_id": f"tnas_pin{key}_temp",
                        "expire_after": 60
                    }
                    discovery_message = ujson.dumps(discovery_payload)
                    mqtt_client.publish(discovery_topic, discovery_message)
                    mqtt_client.publish(f"homeassistant/sensor/tnas_pin{key}/temp", str(temp))
                    print(f"Published tnas_pin{key} temp: {temp}C")

                gc.collect()
                await uasyncio.sleep(0.8)


            else:
                print("No WiFi, reconnecting...")
                await uasyncio.sleep(30)
                
    except OSError as e:
        print(f"MQTT Error: {e}")
        await uasyncio.sleep(30)  # Retry after delay
        uasyncio.create_task(mqtt_publish())  # Restart function if MQTT fails  
        await uasyncio.sleep(30)
# endregion

# region pwm read
def rpm_interrupt(pin):
    global pulse_count
    pulse_count += 1  # Count each falling edge

rpm_sensor.irq(trigger=Pin.IRQ_FALLING, handler=rpm_interrupt)

async def measure_rpm():
    global pulse_count
    global rpm
    while True:
        rpm = (pulse_count / 2) * 60  # Convert to RPM (assuming 2 pulses per rev)
        print(f"Fan Speed: {int(rpm)} rpm")
        pulse_count = 0
        await uasyncio.sleep(1)
# endregion


# region event loops
def start_event_loops():
    event_loop = uasyncio.get_event_loop()
    event_loop.create_task(wifi_connect())
    event_loop.create_task(read_temps())
    event_loop.create_task(mqtt_publish())
    event_loop.create_task(measure_rpm())
    event_loop.run_forever()
# endregion

# region main
if __name__ == "__main__":
    read_fan_settings()  # Read fan settings on startup
    start_event_loops()  # Start the asynchronous event loop
# endregion
