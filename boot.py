import network
import time
import webrepl
import secrets  # Assuming secrets contains WIFI_SSID and WIFI_PWD

def connect_wifi():
    # Initialize the station interface
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    # Connect to the Wi-Fi network
    print("Connecting to WiFi...")
    sta_if.connect(secrets.WIFI_SSID, secrets.WIFI_PWD)

    # Wait until the connection is established
    max_retries = 10
    retries = 0
    while not sta_if.isconnected():
        if retries >= max_retries:
            print("Failed to connect to WiFi, retrying...")
            retries = 0  # Reset retries for the next attempt
        time.sleep(1)
        retries += 1

    # Once connected, print the IP address
    print("Connected to WiFi, IP address:", sta_if.ifconfig()[0])
    
    webrepl.start()

# Call the function to connect to Wi-Fi
connect_wifi()
