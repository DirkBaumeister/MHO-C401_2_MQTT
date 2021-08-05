import time
import paho.mqtt.client as mqtt
from bluepy import btle

mqtt_host = "<MQTT_HOST>"
mqtt_port = 1883

mac_addr = "XX:XX:XX:XX:XX:XX"

ha_topic_temperature = "<MQTT_TOPIC_TEMPERATURE>"
ha_topic_humidity = "<MQTT_TOPIC_HUMIDITY>"
ha_topic_battery = "<MQTT_TOPIC_BATTERY>"

temperature_g = ""
humidity_g = ""
battery_g = ""

client = mqtt.Client()
device = btle.Peripheral()

client.connect(mqtt_host, mqtt_port, 60)

class Delegate(btle.DefaultDelegate):
  def handleNotification(self, cHandle, data):
    global temperature_g
    global humidity_g
    temperature_bytes = data[:2]
    humidity_bytes = data[2]
    temperature = int.from_bytes(temperature_bytes, byteorder="little") / 100.0
    humidity = humidity_bytes

    temperature_g = temperature
    humidity_g = humidity

    client.publish(ha_topic_temperature, payload=temperature, retain=True)
    client.publish(ha_topic_humidity, payload=humidity, retain=True)

try:
  connected_to_peripheral = False
  connection_attempts = 0
  while not connected_to_peripheral:
     if connection_attempts > 5:
        break
     try:
        device.connect(mac_addr)
        connected_to_peripheral = True
        print("Connected!")
     except BaseException as e:
        connection_attempts += 1
        print("Connection failed: " + str(e))
        time.sleep(1)
        print("Retrying...")

  if connected_to_peripheral:
     device.setDelegate(Delegate())
     ch = device.getCharacteristics(uuid="EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6")[0]
     desc = ch.getDescriptors(forUUID=0x2902)[0]
     desc.write(0x01.to_bytes(2, byteorder="little"), withResponse=True)

     batteryLevel = device.getCharacteristics(uuid="00002a19-0000-1000-8000-00805f9b34fb")[0].read()
     client.publish(ha_topic_battery, payload=ord(batteryLevel), retain=True)

     battery_g = ord(batteryLevel)

     # waiting to notification
     while True:
       if not device.waitForNotifications(5.0):
         break

     print("=== Data ===")
     print("Temperature: {}°C".format(temperature_g))
     print("   Humidity: {}%".format(humidity_g))
     print("    Battery: {}%".format(battery_g))
     print("Data published!")

finally:
  device.disconnect()
  client.disconnect()
