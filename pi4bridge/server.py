
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import Advertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.services.standard.device_info import DeviceInfoService
from adafruit_ble_adafruit.adafruit_service import AdafruitServerAdvertisement
from adafruit_ble_adafruit.temperature_service import TemperatureService
from adafruit_ble_adafruit.humidity_service import HumidityService
from adafruit_ble_adafruit.light_sensor_service import LightSensorService

import time
import requests

from secrets import secrets  # pylint: disable=no-name-in-module


aio_auth_header = {"X-AIO-KEY": secrets["aio_key"]}
aio_base_url = "https://io.adafruit.com/api/v2/" + secrets["aio_username"]


def aio_post(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.post(aio_base_url + path, **kwargs)


def aio_get(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.get(aio_base_url + path, **kwargs)

def create_group(name):
    response = aio_post("/groups", json={"name": name})
    if response.status_code != 201:
        print(name)
        print(response.content)
        print(response.status_code)
        raise RuntimeError("unable to create new group")
    return response.json()["key"]


def create_feed(group_key, name):
    response = aio_post(
        "/groups/{}/feeds".format(group_key), json={"feed": {"name": name}}
    )
    if response.status_code != 201:
        print(name)
        print(response.content)
        print(response.status_code)
        raise RuntimeError("unable to create new feed")
    return response.json()["key"]


def create_data(group_key, data):
    response = aio_post("/groups/{}/data".format(group_key), json={"feeds": data})
    if response.status_code == 429:
        print("Throttled!")
        return False
    if response.status_code != 200:
        print(response.status_code, response.json())
        raise RuntimeError("unable to create new data")
    response.close()
    return True


ble = BLERadio()
existing_feeds={}
response = aio_get("/groups")
for group in response.json():
    if "-" not in group["key"]:
        continue
    pieces = group["key"].split("-")
    if len(pieces) != 4 or pieces[0] != "bridge" or pieces[2] != "sensor":
        continue
    _, bridge, _, sensor_address = pieces

    existing_feeds[sensor_address] = []
    for feed in group["feeds"]:
        feed_key = feed["key"].split(".")[-1]
        existing_feeds[sensor_address].append(feed_key)

print(existing_feeds)


while True:
    print("scanning......")
    for adv in ble.start_scan(AdafruitServerAdvertisement):
        print("{} : {}".format(adv.complete_name,adv.connectable))
        if adv.connectable:
            try:
                reversed_address = [adv.address.address_bytes[i] for i in range(5, -1, -1)]
                sensor_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(*reversed_address)
                print(sensor_address)
                group_key = "bridge-{}-sensor-{}".format("pi", sensor_address)
                if sensor_address not in existing_feeds:
                    create_group("Bridge {} Sensor {}".format("pi", sensor_address))
                    create_feed(group_key,"temperature")
                    create_feed(group_key,"humidity")
                    create_feed(group_key,"light")

                connection = ble.connect(adv)
                print(connection.connected)
                data=[]
                try:
                    if TemperatureService in connection:
                        print("found Temperature")
                        temp = connection[TemperatureService]
                        data.append({"key":"temperature","value":temp.temperature})
                        print("temperture: {}".format(temp.temperature) )
                    else:
                        print("did not found temperature service")

                    if HumidityService in connection:
                        print("found HumidityService")
                        hum = connection[HumidityService]
                        data.append({"key":"humidity","value":hum.humidity})
                        print("Humidity: {}".format(hum.humidity) )
                    else:
                        print("did not found HumidityService")
                    
                    if LightSensorService in connection:
                        print("found LightSensorService")
                        ligth = connection[LightSensorService]
                        data.append({"key":"light","value":ligth.light_level})
                        print("LightSensor: {}".format(ligth.light_level) )
                    else:
                        print("did not found LightSensorService")
                    connection.disconnect()
                    for feed_data in data:
                        if feed_data["key"] not in existing_feeds[sensor_address]:
                            create_feed(group_key, feed_data["key"])
                            existing_feeds[sensor_address].append(feed_data["key"])
                    print(group_key, data)
                    if create_data(group_key,data):
                        print("sent to IO adafruits")


                except:
                    connection.disconnect()
            except:
                print("failed connect")
    time.sleep(10)