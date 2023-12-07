"""MQTT bridge.

Polls the local database and publishes changes to an external MQTT broker for Home Assistant.
Accepts changes from Home Assistant and updates the local database.
Supports Home Assistant discovery.
"""
import configparser
import json
import os
import re
import time

import paho.mqtt.client as mqtt
import pymysql.cursors

ENTITIES_CONFIG = {
    "charging_enable": {
        "component": "switch",
        "config": {
            "name": "Charging enable",
            "payload_on": 1,
            "payload_off": 0,
            "command_topic": "~/set",
            "icon": "mdi:ev-station",
        },
    },
    "lock": {
        "component": "lock",
        "config": {
            "name": "Lock",
            "payload_lock": 1,
            "payload_unlock": 0,
            "state_locked": 1,
            "state_unlocked": 0,
            "command_topic": "~/set",
        },
    },
    "max_charging_current": {
        "component": "number",
        "config": {
            "name": "Max charging current",
            "command_topic": "~/set",
            "min": 6,
            "max": 40,
            "unit_of_measurement": "A",
            "device_class": "current",
        },
    },
    "cable_connected": {
        "component": "binary_sensor",
        "config": {
            "name": "Cable connected",
            "payload_on": 1,
            "payload_off": 0,
            "icon": "mdi:ev-plug-type1",
            "device_class": "plug",
        },
    },
    # TODO: Uncomment after fixing.
    # Commented out because it doesn't reset to 0 in db after done charging or paused.
    # "charging_power": {
    #     "component": "sensor",
    #     "config": {
    #         "name": "Charging power",
    #         "device_class": "power",
    #         "unit_of_measurement": "W",
    #         "state_class": "total",
    #         "suggested_display_precision": 1,
    #     },
    # },
    "added_energy": {
        "component": "sensor",
        "config": {
            "name": "Added energy",
            "device_class": "energy",
            "unit_of_measurement": "Wh",
            "state_class": "total",
            "suggested_display_precision": 1,
        },
    },
    "added_range": {
        "component": "sensor",
        "config": {
            "name": "Added range",
            "device_class": "distance",
            "unit_of_measurement": "km",
            "state_class": "total",
            "suggested_display_precision": 1,
            "icon": "mdi:map-marker-distance",
        },
    },
}

DB_QUERY = """
SELECT
  `charging_enable`,
  `lock`,
  `max_charging_current`,
  `was_connected` AS cable_connected,
  `charging_power`,
  GREATEST(`energy_total`, `charged_energy` - `start_charging_energy_tms`) AS added_energy,
  `charged_range` AS added_range
FROM `wallbox_config`, `active_session`, `power_outage_values`;
"""

UPDATEABLE_WALLBOX_CONFIG_FIELDS = ["charging_enable", "lock", "max_charging_current"]

connection = pymysql.connect(
    host="localhost",
    user="root",
    password="fJmExsJgmKV7cq8H",
    db="wallbox",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)
# Because the transaction isolation is set to REPEATABLE-READ we need to commit after every write and read.
# If it was READ-COMMITTED this would only be needed after every write.
# Check the transaction isolation with:
# "SELECT @@GLOBAL.tx_isolation, @@tx_isolation;"
connection.autocommit(True)

mqttc = mqtt.Client()

try:
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "bridge.ini"))
    mqtt_host = config["mqtt"]["host"]
    mqtt_port = int(config["mqtt"]["port"])
    mqtt_username = config["mqtt"]["username"]
    mqtt_password = config["mqtt"]["password"]
    polling_interval_seconds = float(config["settings"]["polling_interval_seconds"])
    device_name = config["settings"]["device_name"]

    with connection.cursor() as cursor:
        cursor.execute("SELECT `serial_num` FROM `charger_info`;")
        result = cursor.fetchone()
        assert result
        serial_num = str(result["serial_num"])

    topic_prefix = "wallbox_" + serial_num
    set_topic = topic_prefix + "/+/set"
    set_topic_re = re.compile(topic_prefix + "/(.*)/set")

    def _on_connect(client, userdata, flags, rc):
        print("Connected to MQTT with", rc)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            mqttc.subscribe(set_topic)
            for k, v in ENTITIES_CONFIG.items():
                unique_id = serial_num + "_" + k
                component = v["component"]
                config = {
                    "~": topic_prefix + "/" + k,
                    "state_topic": "~/state",
                    "unique_id": unique_id,
                    "device": {
                        "identifiers": serial_num,
                        "name": device_name,
                    },
                }
                config = {**v["config"], **config}
                mqttc.publish(
                    "homeassistant/" + component + "/" + unique_id + "/config",
                    json.dumps(config),
                    retain=True,
                )

    def _on_message(client, userdata, message):
        m = set_topic_re.match(message.topic)
        if m:
            field = m.group(1)
            if field in UPDATEABLE_WALLBOX_CONFIG_FIELDS:
                print("Setting:", field, message.payload)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE `wallbox_config` SET `" + field + "`=%s;",
                        (message.payload),
                    )
            else:
                print("Setting unsupported:", field, message.payload)

    mqttc.on_connect = _on_connect
    mqttc.on_message = _on_message
    mqttc.username_pw_set(mqtt_username, mqtt_password)
    print("Connecting to MQTT", mqtt_host, mqtt_port)
    mqttc.connect_async(mqtt_host, mqtt_port)
    mqttc.loop_start()

    published = {}
    while True:
        if mqttc.is_connected():
            with connection.cursor() as cursor:
                cursor.execute(DB_QUERY)
                result = cursor.fetchone()
                assert result
            for key, val in result.items():
                if published.get(key) != val:
                    print("Publishing:", key, val)
                    mqttc.publish(topic_prefix + "/" + key + "/state", val, retain=True)
                    published[key] = val
        time.sleep(polling_interval_seconds)

finally:
    connection.close()
    mqttc.loop_stop()
