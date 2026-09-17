# Altilia EMS Home Assistant integration

This custom integration polls an Altilia EMS HTTP API and exposes its battery,
solar, grid, load, inverter, energy, status, and fault values in Home Assistant.

## Installation

Copy this directory to:

```text
<Home Assistant configuration>/custom_components/altilia/
```

The directory must be named `altilia`; Home Assistant loads the integration from
that package name. Restart Home Assistant, then add **Altilia EMS** from
**Settings > Devices & services > Add integration**.

The device must expose:

```text
GET http://<host>:<port>/api/v1/status
```

`/api/v1/info` is optional and supplies the device name, model, firmware, and
stable device identifier. The integration defaults to port `80` and polls every
10 seconds. The polling interval can be changed from the integration options.
