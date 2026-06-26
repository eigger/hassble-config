# HassBle Config

> This repository stores the device configuration (`config.yaml`) for the [HassBle](https://github.com/eigger/hassble-android) Android app.

**[한국어 문서 → README.ko.md](README.ko.md) | [Contributing Guide → CONTRIBUTING.md](CONTRIBUTING.md)**

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Quick Start](#quick-start)
3. [Root Structure](#root-structure)
4. [defaults — Publish Rules](#defaults--publish-rules)
5. [Device Types](#device-types)
6. [source: advertisement — BLE Passive Scan](#source-advertisement--ble-passive-scan)
   - [match — Matching Conditions](#match--matching-conditions)
   - [instance_mode — Entity Strategy](#instance_mode--entity-strategy)
7. [source: gatt_notify — Active GATT Connection](#source-gatt_notify--active-gatt-connection)
8. [source: obd — ELM327 OBD Polling](#source-obd--elm327-obd-polling)
9. [sensors — Sensor Config](#sensors--sensor-config)
   - [decode — Binary Decoding](#decode--binary-decoding)
   - [Data Types](#data-types)
10. [controls — HA Controls](#controls--ha-controls)
11. [publish — Per-Sensor Filter](#publish--per-sensor-filter)
12. [OBD Preset List](#obd-preset-list)
13. [Full Examples](#full-examples)
14. [Tips & Gotchas](#tips--gotchas)
15. [Contributing](#contributing)

---

## Repository files

| File | Purpose |
|------|---------|
| `config.yaml` | Active gateway configuration (devices the app runs) |
| `templates.yaml` | Device templates for **Import template** in the Sensors tab |

The app loads both from the repo root on the selected branch (`owner/repo` + branch — file names are fixed).

## How It Works

The HassBle app downloads `config.yaml` and `templates.yaml` from this repository (fixed file names at repo root), decodes BLE data according to the rules you define, and automatically declares sensors in Home Assistant via the [ws_bridge](https://github.com/eigger/hass-ws-bridge) integration. No code changes are needed — just edit YAML and push.

Raw URLs (branch `main`):

- Config: `https://raw.githubusercontent.com/eigger/hassble-config/main/config.yaml`
- Templates: `https://raw.githubusercontent.com/eigger/hassble-config/main/templates.yaml`

```
Android Phone (BLE Scan)
       │  raw bytes
       ▼
  HassBle App  ──── config.yaml (this repo) ────▶  decode rules
       │  decoded value
       ▼
  HA WebSocket API  ──────────────────────────────▶  ws_bridge
       │
       ▼
  Home Assistant Entity (sensor / switch / number / …)
```

---

## Quick Start

1. Fork or copy this repository to your GitHub account.
2. Edit `config.yaml` to describe your BLE devices. Optionally add device blocks to `templates.yaml` for **Import template** in the app.
3. In the HassBle app → **Sensors tab** → enter `your-username/hassble-config` and branch `main` (loads `config.yaml` + `templates.yaml` automatically).
4. In the **Gateway tab**, enter your HA URL and token (or use OAuth login), then start the gateway.
5. In the **Sensors tab**, enable the sensors you want and they will appear in Home Assistant.

> ⚠️ **Never put HA credentials (URL / Token) in this file.**  
> Enter them only in the app settings.

---

## Root Structure

```yaml
version: 1

defaults:
  publish:
    on_change_only: true
    min_interval: 10s

devices:
  - id: ...
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | int | `1` | Schema version. Always `1`. |
| `defaults.publish` | object | see below | Default publish filter applied to all sensors. |
| `devices` | list | `[]` | List of device configurations. |

---

## defaults — Publish Rules

Controls how often and under what conditions sensor values are sent to HA. Can be overridden per-device or per-sensor.

```yaml
defaults:
  publish:
    on_change_only: true   # Only send when value changes (default: true)
    min_interval: 10s      # Minimum time between sends (default: 10s)
    heartbeat: 5m          # Force a send at this interval even if unchanged (optional)
    deadband: 0.5          # Ignore changes smaller than this (optional, numeric sensors only)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `on_change_only` | bool | `true` | Only send when the value changes. |
| `min_interval` | duration | `10s` | Minimum time between two sends. Formats: `500ms`, `30s`, `5m`. |
| `heartbeat` | duration | `null` | Even if unchanged, force a send at this interval. |
| `deadband` | float | `null` | Ignore changes smaller than this value (numeric sensors). |

---

## Device Types

Every entry in `devices` must have a `source` field that selects the data path.

| `source` | Description |
|----------|-------------|
| `advertisement` | Passive BLE scan — no connection, reads broadcast packets. |
| `gatt_notify` | Active GATT connection — connects to the device and subscribes to notifications. Supports write commands. |
| `obd` | ELM327 OBD adapter over BLE — polls PID commands and parses ISO-TP responses. |

**Common fields shared by all device types:**

```yaml
- id: my_device          # Unique identifier (lowercase letters, digits, _)
  name: "My Device"      # Display name (HA device name)
  source: advertisement  # advertisement | gatt_notify | obd
  publish:               # (optional) Override publish rules for all sensors of this device
    on_change_only: true
    min_interval: 5s
  sensors: [...]
  controls: [...]        # gatt_notify / obd only
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique identifier. Used in HA entity unique_id. Use lowercase letters, digits, `_`. |
| `name` | string | ✅ | Display name shown in HA device. |
| `source` | enum | ✅ | Data source type (see above). |
| `publish` | object | ❌ | Device-level publish rule override. |
| `sensors` | list | ❌ | List of sensor definitions. |
| `controls` | list | ❌ | List of control definitions. |

---

## source: advertisement — BLE Passive Scan

Listens for BLE advertisement packets without connecting. Use `match` to filter packets.

```yaml
- id: my_sensor
  name: "My BLE Sensor"
  source: advertisement
  instance_mode: mac      # mac | shared (see below)
  match:
    manufacturer_id: 76   # Apple = 76 (0x004C) — must use decimal
    manufacturer_min_length: 24
    manufacturer_hex_prefix: "0215"
  sensors:
    - key: temperature
      source_field: manufacturer_data   # manufacturer_data | service_data | raw
      decode:
        offset: 18
        length: 2
        type: uint16
        endian: big
        scale: 0.002670288
        offset_value: -45
```

### match — Matching Conditions

All specified conditions must be satisfied simultaneously (AND logic). Unspecified fields are ignored.

| Field | Type | Description |
|-------|------|-------------|
| `mac` | string | Fixed MAC address filter. Format: `"AA:BB:CC:DD:EE:FF"`. |
| `service_data_uuid` | string | 16-bit or 128-bit service UUID suffix. E.g. `"F51C"`, `"181A"`. |
| `manufacturer_id` | int | Manufacturer company ID. **Must use decimal** (not `0x...`). E.g. Apple=`76`. |
| `manufacturer_hex_prefix` | string | Manufacturer payload (hex string) must start with this prefix. E.g. iBeacon=`"0215"`. |
| `manufacturer_min_length` | int | Minimum byte length of the manufacturer payload. |
| `name_prefix` | string | BLE device name must start with this string. |

> **⚠️ Hex literals warning**  
> The YAML parser (`kaml`) may silently fail with `0x...` hex values. Always use **decimal integers**.  
> `0x004C` → `76`, `0x035D` → `861`

### instance_mode — Entity Strategy

Determines how HA entities are created when multiple devices of the same type are detected.

| Value | Description |
|-------|-------------|
| `mac` (default) | Each unique MAC address creates its own set of HA entities. Entity unique_id: `{device_id}_{MAC}_temperature` etc. Bind a specific MAC in the app's Sensors tab to pre-declare entities before the device is seen. |
| `shared` | All matching advertisers share a single HA entity. The last received packet overwrites the state. Useful for parking beacons, clickers, etc. |

---

## source: gatt_notify — Active GATT Connection

Connects to a specific BLE device, subscribes to a GATT characteristic, and receives notifications. Optionally sends hex commands back.

```yaml
- id: custom_meter
  name: "Custom BLE Meter"
  source: gatt_notify
  gatt:
    mac: "AA:BB:CC:DD:EE:FF"   # Or bind in the app's Sensors tab
    service_uuid: "ffe0"
    notify_char_uuid: "ffe1"
    write_char_uuid: "ffe2"    # Optional — required for controls
    auto_connect: true
  sensors:
    - key: power
      unit: "W"
      device_class: power
      state_class: measurement
      decode: { offset: 0, length: 2, type: uint16, endian: little }
  controls:
    - key: relay
      type: switch
      command: { on: "A10100", off: "A10000" }
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mac` | string | ❌ | Device MAC address. Can also be set via app bind. |
| `service_uuid` | string | ✅ | GATT service UUID (16-bit or full 128-bit). |
| `notify_char_uuid` | string | ✅ | Characteristic to subscribe for notifications. |
| `write_char_uuid` | string | ❌ | Characteristic to write commands to (needed for controls). |
| `auto_connect` | bool | ❌ | Automatically reconnect on disconnect. Default `true`. |

> If `mac` is not set in the YAML, bind the device in the app's **Sensors tab** (tap "Connect / Bind" next to the device).

---

## source: obd — ELM327 OBD Polling

Connects to an ELM327 BLE adapter, sends OBD-II (and GM mode 22) PID commands, and parses ISO-TP responses. Use built-in `preset`s or define custom `mode`/`pid`/`formula`.

```yaml
- id: car_obd
  name: "Vehicle OBD"
  source: obd
  obd:
    # mac: "AA:BB:CC:DD:EE:FF"  # Or bind in the app
    service_uuid: "18F0"
    tx_char_uuid: "2AF1"
    rx_char_uuid: "2AF0"
    tx_delay: 50ms
    init_commands:
      - "ATZ"
      - "ATE0"
      - "ATL0"
      - "ATS0"
      - "ATH0"
      - "ATSP6"     # Protocol: ATSP0=auto, ATSP6=ISO 15765-4 CAN 500kbps
  sensors:
    # Using preset (recommended)
    - { key: rpm,   preset: rpm,   update_interval: 1s }
    - { key: speed, preset: speed, update_interval: 1s }
    # Custom definition
    - key: custom_pid
      mode: "01"
      pid: "0C"
      formula: "(a*256+b)/4"
      unit: "rpm"
      state_class: measurement
      update_interval: 1s
```

| Field | Type | Default | Description |
|-------|------|---------|-|
| `mac` | string | — | Adapter MAC. Set here or via app bind. |
| `service_uuid` | string | `"FFF0"` | BLE GATT service UUID. |
| `tx_char_uuid` | string | `"FFF2"` | Write characteristic (send commands). |
| `rx_char_uuid` | string | `"FFF1"` | Notify characteristic (receive responses). |
| `tx_delay` | duration | `50ms` | Delay between consecutive commands. |
| `init_commands` | list | `[]` | Commands sent once on each connection before polling starts. |
| `auto_connect` | bool | `true` | Automatically reconnect on disconnect. |

**OBD sensor-specific fields:**

| Field | Type | Description |
|-------|------|-------------|
| `preset` | string | Use a built-in preset (see table below). |
| `mode` | string | OBD mode. `"01"` = standard, `"22"` = manufacturer specific. Default `"01"`. |
| `pid` | string | PID hex code (without mode prefix). E.g. `"0C"`, `"199A"`. |
| `formula` | string | Math expression. Variables `a`,`b`,`c`,`d` are response bytes. E.g. `"(a*256+b)/4"`. |
| `update_interval` | duration | How often to poll this PID. Default `60s`. |
| `pre_commands` | list | Extra AT/OBD commands to send before this PID (e.g., header switch for GM). |

---

## sensors — Sensor Config

Each item in the `sensors` list defines one HA entity.

```yaml
sensors:
  - key: temperature           # Required — unique key within the device
    platform: sensor           # sensor | binary_sensor | text_sensor
    device_class: temperature  # HA device_class (optional)
    unit: "°C"
    state_class: measurement   # measurement | total | total_increasing
    icon: "mdi:thermometer"
    entity_category: diagnostic # diagnostic | config (omit for normal sensor)
    accuracy_decimals: 2
    source_field: manufacturer_data  # advertisement only
    min_length: 24
    decode:
      offset: 18
      length: 2
      type: uint16
      endian: big
      scale: 0.002670288
      offset_value: -45
    publish:                   # Override publish rule for this sensor only
      deadband: 0.1
      min_interval: 30s
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | string | ✅ | Unique key within the device. Becomes part of HA entity unique_id. |
| `platform` | string | ❌ | HA entity platform. Default `sensor`. |
| `device_class` | string | ❌ | HA device class (temperature, humidity, battery, voltage, …). |
| `unit` | string | ❌ | Unit of measurement shown in HA. |
| `state_class` | string | ❌ | HA state class for statistics. |
| `icon` | string | ❌ | MDI icon string, e.g. `"mdi:thermometer"`. |
| `entity_category` | string | ❌ | `diagnostic` or `config`. Omit for normal sensor. |
| `accuracy_decimals` | int | ❌ | Round the decoded value to N decimal places. |
| `source_field` | enum | ❌ | `manufacturer_data` / `service_data` / `raw`. Default `raw`. |
| `min_length` | int | ❌ | Skip this sensor if the payload is shorter than N bytes. |
| `decode` | object | ❌ | Binary decoding rules. See below. |
| `publish` | object | ❌ | Override publish rule for this sensor only. |

### decode — Binary Decoding

Extracts a numeric or string value from a raw byte array.

**Formula:** `final_value = (raw_integer * scale) + offset_value`

```yaml
decode:
  offset: 18          # Byte offset (0-based)
  length: 2           # Number of bytes to read
  type: uint16        # Data type (see table below)
  endian: big         # big | little
  bitmask: 0x0F       # (optional) Apply AND bitmask before decoding
  scale: 0.1          # (optional) Multiply factor. Default 1.0
  offset_value: -40   # (optional) Add after scaling. Default 0.0
  map:                # (optional) Map integer result to string
    "0": "off"
    "1": "on"
    "2": "standby"
```

| Field | Type | Default | Description |
|-------|------|---------|-|
| `offset` | int | `0` | Start byte index (0-based). |
| `length` | int | `1` | Number of bytes to read. |
| `type` | enum | `uint8` | Data type to interpret the bytes as. |
| `endian` | enum | `big` | Byte order. `big` = MSB first, `little` = LSB first. |
| `bitmask` | int | `null` | Apply AND bitmask to the raw integer before scaling. |
| `scale` | float | `1.0` | Multiply the raw integer by this value. |
| `offset_value` | float | `0.0` | Add this after scaling: `(raw * scale) + offset_value`. |
| `map` | object | `{}` | Map integer result to a string. Keys must be quoted strings. |

### Data Types

| Type | Bytes | Description |
|------|-------|-------------|
| `uint8` | 1 | Unsigned 8-bit integer (0–255). |
| `int8` | 1 | Signed 8-bit integer (-128–127). |
| `uint16` | 2 | Unsigned 16-bit integer (0–65535). |
| `int16` | 2 | Signed 16-bit integer (-32768–32767). |
| `uint32` | 4 | Unsigned 32-bit integer. |
| `int32` | 4 | Signed 32-bit integer. |
| `float32` | 4 | IEEE 754 single-precision float. |
| `timestamp` | 4 | Bytes interpreted as month/day/hour/minute (1 byte each). Returned as ISO 8601 string. |
| `string` | N | Bytes decoded as ASCII. Use with `platform: text_sensor`. |

---

## controls — HA Controls

Define Home Assistant entities that send BLE write commands when triggered from HA. Only available for `gatt_notify` and `obd` sources.

```yaml
controls:
  # Switch — on/off hex command
  - key: relay
    type: switch
    name: "Main Relay"
    icon: "mdi:electric-switch"
    entity_category: config
    command:
      on:  "A10100"
      off: "A10000"

  # Number — insert value into hex template
  - key: brightness
    type: number
    min: 0
    max: 100
    step: 1
    command:
      template: "B2{value:02X}FF"

  # Select — per-option hex command
  - key: mode
    type: select
    options: ["auto", "cool", "heat", "fan"]
    command:
      auto: "C000"
      cool: "C001"
      heat: "C002"
      fan:  "C003"

  # Button — sends hex on press
  - key: restart
    type: button
    command:
      press: "FFFE"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | string | ✅ | Unique key within the device. |
| `type` | enum | ✅ | `switch` / `number` / `select` / `button`. |
| `name` | string | ❌ | Display name in HA. Auto-generated from key if omitted. |
| `icon` | string | ❌ | MDI icon string. |
| `entity_category` | string | ❌ | `config` or `diagnostic`. |
| `command` | object | ✅ | Command map. Keys depend on type (see examples above). |
| `options` | list | select only | Options list for `select` type. |
| `min` | float | number only | Minimum value for `number` type. |
| `max` | float | number only | Maximum value for `number` type. |
| `step` | float | ❌ | Step size for `number` type. |

**command template placeholders:**

| Placeholder | Description |
|-------------|-------------|
| `{value}` | Integer value (decimal). |
| `{value:02X}` | Value as 2-digit uppercase hex (zero-padded). |
| `{value:04X}` | Value as 4-digit uppercase hex. |

---

## publish — Per-Sensor Filter

Override the global `defaults.publish` for a specific sensor. Useful for sensors that change slowly (fuel level) or need frequent updates (RPM).

```yaml
sensors:
  - key: fuel_level
    preset: fuel_level
    update_interval: 30s
    publish:
      on_change_only: true
      deadband: 0.5
      min_interval: 60s
      heartbeat: 30m
```

**Priority:** sensor `publish` > device `publish` > `defaults.publish`

---

## OBD Preset List

Use `preset: <name>` in OBD sensors to use these built-in definitions. You can override individual fields (`unit`, `accuracy_decimals`, etc.) after specifying the preset.

### Standard OBD-II (mode 01)

| Preset | PID | Formula | Unit | Description |
|--------|-----|---------|------|-------------|
| `rpm` | `0C` | `(a*256+b)/4` | rpm | Engine RPM |
| `speed` | `0D` | `a` | km/h | Vehicle speed |
| `engine_load` | `04` | `a/2.55` | % | Engine load |
| `throttle` | `11` | `a/2.55` | % | Throttle position |
| `coolant_temp` | `05` | `a-40` | °C | Coolant temperature |
| `intake_air_temp` | `0F` | `a-40` | °C | Intake air temperature |
| `ambient_temp` | `46` | `a-40` | °C | Ambient temperature |
| `battery_voltage` | `42` | `(a*256+b)/1000` | V | Battery voltage |
| `run_time` | `1F` | `a*256+b` | s | Engine run time |
| `fuel_level` | `2F` | `a/2.55` | % | Fuel level |
| `actual_torque` | `62` | `a-125` | % | Actual torque |
| `odometer` | `A6` | `(a*16777216+b*65536+c*256+d)/10` | km | Odometer |

### GM Extensions (mode 22)

| Preset | PID | Formula | Unit | Description |
|--------|-----|---------|------|-------------|
| `gm_current_gear` | `199A` | `a` | — | Current gear |
| `gm_prnd_status_alt` | `2889` | `a` | — | PRND status |
| `gm_oil_pressure` | `115C` | `(a*0.65)-17.5` | psi | Oil pressure |
| `gm_trans_temp` | `1940` | `a-40` | °C | Transmission temperature |
| `gm_fuel_level_liters` | `132A` | `(a*256+b)/64` | L | Fuel level (liters) |

---

## Full Examples

### Example 1 — Jaalee JHT (iBeacon Temperature/Humidity)

```yaml
- id: jaalee_jht
  name: "Jaalee JHT"
  source: advertisement
  instance_mode: mac
  match:
    manufacturer_id: 76          # Apple Inc. (must be decimal)
    manufacturer_min_length: 24
    manufacturer_hex_prefix: "0215"   # iBeacon type marker
  sensors:
    - key: temperature
      device_class: temperature
      unit: "°C"
      state_class: measurement
      accuracy_decimals: 2
      source_field: manufacturer_data
      decode: { offset: 18, length: 2, type: uint16, endian: big, scale: 0.002670288, offset_value: -45 }
    - key: humidity
      device_class: humidity
      unit: "%"
      state_class: measurement
      accuracy_decimals: 2
      source_field: manufacturer_data
      decode: { offset: 20, length: 2, type: uint16, endian: big, scale: 0.001524504 }
    - key: battery
      device_class: battery
      unit: "%"
      state_class: measurement
      source_field: manufacturer_data
      decode: { offset: 23, length: 1, type: uint8 }
```

### Example 2 — Custom Service Data Sensor

```yaml
- id: my_env_sensor
  name: "Environment Sensor"
  source: advertisement
  instance_mode: shared
  match:
    service_data_uuid: "181A"     # Environmental Sensing UUID
  sensors:
    - key: temperature
      device_class: temperature
      unit: "°C"
      state_class: measurement
      accuracy_decimals: 1
      source_field: service_data
      decode: { offset: 0, length: 2, type: int16, endian: little, scale: 0.01 }
    - key: humidity
      device_class: humidity
      unit: "%"
      state_class: measurement
      accuracy_decimals: 1
      source_field: service_data
      decode: { offset: 2, length: 2, type: uint16, endian: little, scale: 0.01 }
    - key: battery
      device_class: battery
      unit: "%"
      source_field: service_data
      decode: { offset: 9, length: 1, type: uint8 }
```

### Example 3 — GATT Sensor with Switch Control

```yaml
- id: power_monitor
  name: "Power Monitor"
  source: gatt_notify
  gatt:
    service_uuid: "ffe0"
    notify_char_uuid: "ffe1"
    write_char_uuid: "ffe2"
  sensors:
    - key: power
      device_class: power
      unit: "W"
      state_class: measurement
      decode: { offset: 0, length: 2, type: uint16, endian: little }
    - key: voltage
      device_class: voltage
      unit: "V"
      state_class: measurement
      accuracy_decimals: 1
      decode: { offset: 2, length: 2, type: uint16, endian: little, scale: 0.1 }
    - key: current
      device_class: current
      unit: "A"
      state_class: measurement
      accuracy_decimals: 2
      decode: { offset: 4, length: 2, type: uint16, endian: little, scale: 0.01 }
  controls:
    - key: relay
      type: switch
      name: "Relay"
      icon: "mdi:electric-switch"
      command: { on: "A10100", off: "A10000" }
```

### Example 4 — OBD with Presets and Custom Publish

```yaml
- id: car_obd
  name: "Vehicle"
  source: obd
  obd:
    service_uuid: "18F0"
    tx_char_uuid: "2AF1"
    rx_char_uuid: "2AF0"
    tx_delay: 50ms
    init_commands: ["ATZ", "ATE0", "ATL0", "ATS0", "ATH0", "ATSP6"]
  sensors:
    - { key: rpm,          preset: rpm,          update_interval: 1s }
    - { key: speed,        preset: speed,        update_interval: 1s }
    - { key: coolant_temp, preset: coolant_temp, update_interval: 10s }
    - key: fuel_level
      preset: fuel_level
      update_interval: 30s
      publish:
        deadband: 1.0
        min_interval: 60s
        heartbeat: 10m
```

### Example 5 — Value Map (Status Codes)

```yaml
- id: status_device
  name: "Status Device"
  source: advertisement
  instance_mode: shared
  match:
    manufacturer_id: 1234
  sensors:
    - key: mode
      platform: text_sensor
      source_field: manufacturer_data
      decode:
        offset: 5
        length: 1
        type: uint8
        map:
          "0": "idle"
          "1": "running"
          "2": "error"
          "3": "standby"
```

---

## Tips & Gotchas

### ⚠️ Always use decimal for manufacturer_id

The YAML parser (`kaml`) may silently parse `0x004C` as `0` or cause a crash. Always convert hex to decimal:

```yaml
# ❌ Wrong — may cause parse errors
manufacturer_id: 0x004C

# ✅ Correct
manufacturer_id: 76       # 0x004C = 76
manufacturer_id: 861      # 0x035D = 861
```

### AND logic in match

All `match` conditions are ANDed together. If you specify both `service_data_uuid` and `manufacturer_id`, the packet must satisfy **both**. Remove a condition if your device doesn't always advertise it.

### instance_mode: mac — Bind for early entity creation

With `instance_mode: mac` and no fixed `match.mac`, HA entities only appear after the device is detected by BLE scan. To make entities appear immediately on gateway connect, bind the MAC in the app's **Sensors tab** → "Connect / Bind".

### source_field selection

For advertisement sensors, choose the right payload source:
- `manufacturer_data` — data after the manufacturer company ID (most common for custom sensors)
- `service_data` — data in the service data AD type (common for standard profiles like 0x181A)
- `raw` — full scan record bytes (rarely needed)

### Duration format

Durations support milliseconds (`ms`), seconds (`s`), and minutes (`m`).

```yaml
tx_delay: 50ms
min_interval: 10s
heartbeat: 5m
update_interval: 1s
```

### Config is cached

The app caches the last successfully loaded config. If the network is unavailable on startup, it uses the cache. The app always shows "Using cached config" in the header when this happens.

---

## Contributing

We welcome your vehicle OBD-II PID configurations! Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to contribute.

---

## License

MIT
