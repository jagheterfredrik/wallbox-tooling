#!/bin/bash

# Un-clouding
systemctl stop mywallbox.service
systemctl stop cloud_command_gateway_srvc.service
systemctl stop cloud_pub_sub_srvc.service
systemctl stop wallbox_login.service
systemctl stop wallbox_cbit.service
systemctl stop wallbox_telemetry.service
systemctl stop telemetry_srvc.service

# Moar!!
systemctl stop blewallbox.service
systemctl stop wallbox_wifi.service
systemctl stop wallboxsmachine.service
systemctl stop software_update.service
systemctl stop ocppwallbox.service
systemctl stop on_time_track.service
systemctl stop resources_monitor.service
systemctl stop power_manager.service
systemctl stop credentials_generator.service
systemctl stop cdc_wrapper_srvc.service
systemctl stop schedule_manager.service
systemctl stop micro2wallbox.service
systemctl stop redis.service
systemctl stop mosquitto.service
systemctl stop mysqld.service
