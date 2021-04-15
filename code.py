from random import randint
import time
import board
import adafruit_ahtx0
import adafruit_dps310
from digitalio import DigitalInOut, Direction, Pull
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
            network.rssi, network.channel))
wifi.radio.stop_scanning_networks()

#apparently this should do reconnections
print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

#test chunk
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)

try:
    # Get the 'temperature' feed from Adafruit IO
    temperature_feed = io.get_feed("gardentemp")
except AdafruitIO_RequestError:
    # If no 'temperature' feed exists, create one
    temperature_feed = io.create_new_feed("gardentemp")

#turn the backlight off
backlight = DigitalInOut(board.TFT_BACKLIGHT)
backlight.direction = Direction.OUTPUT

select = DigitalInOut(board.BUTTON_SELECT)
select.direction = Direction.INPUT

# Create the sensor object using I2C
sensor = adafruit_ahtx0.AHTx0(board.I2C())
dps310 = adafruit_dps310.DPS310(board.I2C())

loop_count=0
while True:
    loop_count = (loop_count+1) % 60
    backlight.value = select.value
    if (loop_count % 10 == 0):
        print("\nAHTTemperature: %0.1f C" % sensor.temperature)
        print("AHTHumidity: %0.1f %%" % sensor.relative_humidity)
        print("DPSTemperature = %.2f *C" % dps310.temperature)
        print("DPSPressure = %.2f hPa" % dps310.pressure)
        print(select.value)
        print("")

    if (loop_count == 0):
        temperature_feed = io.get_feed("gardentemp")
        humid_feed = io.get_feed("gardenhumid")

        print("Sending {0} to temperature feed...".format(sensor.temperature))
        io.send_data(temperature_feed["key"], dps310.temperature)
        print("Data sent!")

        print("Sending {0} to humidity feed...".format(sensor.relative_humidity))
        io.send_data(humid_feed["key"], sensor.relative_humidity)
        print("Data sent!")


    time.sleep(1)