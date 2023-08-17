#!/bin/bash

# Un-clouding
systemctl stop mywallbox.service
systemctl stop cloud_command_gateway_srvc.service
systemctl stop cloud_pub_sub_srvc.service
systemctl stop wallbox_login.service
systemctl stop wallbox_cbit.service
systemctl stop wallbox_telemetry.service
systemctl stop telemetry_srvc.service
