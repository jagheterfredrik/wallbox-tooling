# wallbox-tooling
Tools and proof of concepts of extending the Wallbox Pulsar Plus. To be uploaded to Wallbox using e.g. scp.

## Proof of concept: Rest API
`python3 local-rest.py`
Test using
`curl http://wallbox-ip:8000/lock`

## Proof of concept: Modbus TCP
`./mbusd -d -p /dev/ttyS0 -L -`

## MQTT Bridge
See README.md in mqtt-proxy directory.

## Tooling
Compiled versions of `gdb`, `interceptty`, `screen` and `tcpdump` compatible with the Wallbox.

## Un-cloud and un-wallbox
Note: Use only if you know what you are doing, the functionality of Wallbox will obviously be affected.
`un-cloud.sh` will disable all services talking to the Wallbox cloud.
`un-wallbox.sh` will disable all Wallbox services.
