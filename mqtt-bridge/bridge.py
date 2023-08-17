import time

import pymysql.cursors
import paho.mqtt.client as mqtt

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='fJmExsJgmKV7cq8H',
                             db='wallbox',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

with connection.cursor() as cursor:
    cursor.execute("select serial_num from charger_info;")
    serial_num = str(cursor.fetchone().get("serial_num"))
    prefix = "homeassistant/sensor/wallbox_" + serial_num + "/"
    stat_suffix = "/state"
    cmd_suffix = "/set"

published = dict()

try:
    with connection.cursor() as cursor:
        def on_message(client, userdata, message):
            if message.topic == prefix + "max_charging_current" + cmd_suffix:
                cursor.execute("UPDATE wallbox_config SET `max_charging_current`=%s;", (message.payload,))
            elif message.topic == prefix + "lock" + cmd_suffix:
                cursor.execute("UPDATE wallbox_config SET `lock`=%s;", (message.payload,))
            else:
                return
            connection.commit()

        def on_connect(client, userdata, flags, rc):
            if rc == mqtt.MQTT_ERR_SUCCESS:
                mqttc.subscribe(prefix + "+" + cmd_suffix)

        mqttc = mqtt.Client()
        mqttc.on_message = on_message
        mqttc.on_connect = on_connect
        mqttc.connect_async("localhost", 1883, 60)
        mqttc.loop_start()

        while 1:
            sql = "SELECT `lock`, `max_charging_current` FROM `wallbox_config`;"
            cursor.execute(sql)
            result = cursor.fetchone()
            for key, val in result.items():
                if key not in published or published.get(key) != val:
                    mqttc.publish(stat_prefix + key, val, retain=True)
                    published[key] = val
            time.sleep(1)

finally:
    mqttc.loop_stop()
    connection.close()
