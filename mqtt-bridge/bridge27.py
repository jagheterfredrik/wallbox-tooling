import time
import threading

import pymysql.cursors
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe

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
    prefix = "/wallbox/" + serial_num + "/"
    stat_prefix = "stat" + prefix
    cmd_prefix = "cmnd" + prefix

def listener_thread():
    with connection.cursor() as cursor:
        def cb(client, userdata, message):
            if message.topic == cmd_prefix + "max_charging_current":
                cursor.execute("update wallbox_config set `max_charging_current`=%s;", (message.payload,))
            elif message.topic == cmd_prefix + "lock":
                cursor.execute("update wallbox_config set `lock`=%s;", (message.payload,))
            connection.commit()

        subscribe.callback(cb, cmd_prefix + "#", hostname="mqtt.eclipseprojects.io")

x = threading.Thread(target=listener_thread, args=tuple())
x.start()

try:
    with connection.cursor() as cursor:

        while 1:
            sql = "SELECT `lock`, `max_charging_current` FROM `wallbox_config`;"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(result)
            for key, val in result.items():
                publish.single(stat_prefix + key, val, hostname="mqtt.eclipseprojects.io")
            time.sleep(1)

finally:
    connection.close()