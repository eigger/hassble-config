#!/usr/bin/env python3
"""
HassBle YAML Configuration and Template Validator
Validates config.yaml and templates.yaml against the HassBle Android schema and ConfigValidator rules.
"""

import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

VALID_SOURCES = {"advertisement", "gatt_notify", "obd"}
VALID_INSTANCE_MODES = {"mac", "shared"}
VALID_SOURCE_FIELDS = {"service_data", "manufacturer_data", "raw"}
VALID_PLATFORMS = {"sensor", "binary_sensor", "text_sensor"}
VALID_DATA_TYPES = {
    "int8", "uint8", "int16", "uint16", "int32", "uint32",
    "float32", "timestamp", "string"
}
VALID_ENDIANS = {"big", "little"}
VALID_CONTROL_TYPES = {"switch", "number", "select", "button"}
VALID_STATE_CLASSES = {"measurement", "measurement_angle", "total", "total_increasing"}
NUMERIC_DEVICE_CLASSES = {
    "battery", "carbon_dioxide", "carbon_monoxide", "current", "distance",
    "duration", "energy", "frequency", "gas", "humidity", "illuminance",
    "moisture", "monetary", "nitrogen_dioxide", "nitrogen_monoxide",
    "nitrous_oxide", "ozone", "pm1", "pm10", "pm25", "power", "power_factor",
    "precipitation", "precipitation_intensity", "pressure", "reactive_energy",
    "reactive_power", "signal_strength", "sound_pressure", "speed",
    "sulphur_dioxide", "temperature", "volatile_organic_compounds",
    "volatile_organic_compounds_parts", "voltage", "volume", "volume_flow_rate",
    "volume_storage", "water", "weight", "wind_speed",
}

KNOWN_DEVICE_KEYS = {
    "id", "name", "source", "match", "instance_mode", "gatt", "obd",
    "sensors", "controls", "publish"
}
KNOWN_MATCH_KEYS = {
    "mac", "service_data_uuid", "manufacturer_id", "manufacturer_hex_prefix",
    "manufacturer_min_length", "name_prefix"
}
KNOWN_GATT_KEYS = {
    "mac", "service_uuid", "notify_char_uuid", "write_char_uuid", "auto_connect"
}
KNOWN_OBD_KEYS = {
    "mac", "service_uuid", "tx_char_uuid", "rx_char_uuid", "tx_delay",
    "init_commands", "default_commands", "auto_connect"
}
KNOWN_SENSOR_KEYS = {
    "key", "name", "platform", "device_class", "unit", "state_class", "icon",
    "entity_category", "accuracy_decimals", "source_field", "length",
    "min_length", "decode", "preset", "mode", "pid", "formula",
    "update_interval", "pre_commands", "publish"
}
KNOWN_DECODE_KEYS = {
    "offset", "length", "type", "endian", "bitmask", "scale",
    "offset_value", "map"
}
KNOWN_CONTROL_KEYS = {
    "key", "type", "name", "icon", "entity_category", "command",
    "options", "min", "max", "step"
}
KNOWN_PUBLISH_KEYS = {
    "on_change_only", "min_interval", "heartbeat", "deadband"
}

class ValidationResult:
    def __init__(self, filename: str):
        self.filename = filename
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, path: str, msg: str):
        self.errors.append(f"[{self.filename}] ERROR at '{path}': {msg}")

    def warning(self, path: str, msg: str):
        self.warnings.append(f"[{self.filename}] WARNING at '{path}': {msg}")

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def check_unknown_keys(data: Dict[str, Any], known_keys: Set[str], path: str, res: ValidationResult):
    if not isinstance(data, dict):
        return
    for k in data.keys():
        if k not in known_keys:
            res.error(f"{path}.{k}", f"Unknown property '{k}'. Allowed keys: {sorted(list(known_keys))}")


def validate_publish(publish: Any, path: str, res: ValidationResult):
    if not isinstance(publish, dict):
        res.error(path, "publish must be an object (map)")
        return
    check_unknown_keys(publish, KNOWN_PUBLISH_KEYS, path, res)
    if "on_change_only" in publish and not isinstance(publish["on_change_only"], bool):
        res.error(f"{path}.on_change_only", "Must be a boolean (true/false)")
    for dur_field in ["min_interval", "heartbeat"]:
        if dur_field in publish:
            val = publish[dur_field]
            if not isinstance(val, str) or not re.match(r"^\d+(ms|s|m|h)$", str(val).strip()):
                res.error(f"{path}.{dur_field}", f"Invalid duration '{val}'. Example: 500ms, 10s, 5m")
    if "deadband" in publish and not isinstance(publish["deadband"], (int, float)):
        res.error(f"{path}.deadband", "deadband must be a number")


def validate_decode(decode: Any, path: str, res: ValidationResult):
    if not isinstance(decode, dict):
        res.error(path, "decode must be an object")
        return
    check_unknown_keys(decode, KNOWN_DECODE_KEYS, path, res)
    
    if "offset" in decode and not isinstance(decode["offset"], int):
        res.error(f"{path}.offset", "offset must be an integer")
    if "length" in decode and not isinstance(decode["length"], int):
        res.error(f"{path}.length", "length must be an integer")
    
    dtype = str(decode.get("type", "uint8")).lower()
    if dtype not in VALID_DATA_TYPES:
        res.error(f"{path}.type", f"Invalid data type '{decode.get('type')}'. Must be one of {sorted(list(VALID_DATA_TYPES))}")
    
    if "endian" in decode:
        endian = str(decode["endian"]).lower()
        if endian not in VALID_ENDIANS:
            res.error(f"{path}.endian", f"Invalid endian '{decode['endian']}'. Must be 'big' or 'little'")
    
    if "scale" in decode and not isinstance(decode["scale"], (int, float)):
        res.error(f"{path}.scale", "scale must be a number")
    if "offset_value" in decode and not isinstance(decode["offset_value"], (int, float)):
        res.error(f"{path}.offset_value", "offset_value must be a number")
    if "map" in decode:
        if not isinstance(decode["map"], dict):
            res.error(f"{path}.map", "map must be a dictionary (key: value)")


def validate_sensor(sensor: Any, device_source: str, path: str, res: ValidationResult):
    if not isinstance(sensor, dict):
        res.error(path, "Sensor must be an object")
        return
    check_unknown_keys(sensor, KNOWN_SENSOR_KEYS, path, res)

    key = sensor.get("key")
    if not key or not isinstance(key, str):
        res.error(f"{path}.key", "Missing or invalid sensor 'key'")
        return

    platform = sensor.get("platform", "sensor")
    if platform not in VALID_PLATFORMS:
        res.error(f"{path}.platform", f"Invalid platform '{platform}'. Must be one of {sorted(list(VALID_PLATFORMS))}")

    is_text = platform == "text_sensor"
    unit = sensor.get("unit")
    state_class = sensor.get("state_class")
    if isinstance(state_class, str) and state_class.lower() == "none":
        state_class = None
    device_class = sensor.get("device_class")
    accuracy_decimals = sensor.get("accuracy_decimals")

    if is_text:
        if unit is not None:
            res.warning(f"{path}.unit", f"unit='{unit}' is ignored for text_sensor")
        if state_class is not None:
            res.warning(f"{path}.state_class", f"state_class='{state_class}' is ignored for text_sensor")
        if accuracy_decimals is not None:
            res.warning(f"{path}.accuracy_decimals", "accuracy_decimals is ignored for text_sensor")
        if device_class in NUMERIC_DEVICE_CLASSES:
            res.warning(f"{path}.device_class", f"device_class='{device_class}' expects numeric value but platform is text_sensor")
    else:
        if state_class is not None and state_class not in VALID_STATE_CLASSES:
            res.error(f"{path}.state_class", f"Invalid state_class '{state_class}'. Must be one of {sorted(list(VALID_STATE_CLASSES))}")
        if unit is not None and state_class is None:
            res.warning(f"{path}.state_class", f"unit='{unit}' set but state_class is missing")
        if state_class is not None and unit is None:
            res.warning(f"{path}.unit", f"state_class='{state_class}' set but unit is missing")
        if device_class == "timestamp" and accuracy_decimals is not None:
            res.warning(f"{path}.accuracy_decimals", "accuracy_decimals is meaningless for timestamp")

    if "source_field" in sensor:
        sf = str(sensor["source_field"]).lower()
        if sf not in VALID_SOURCE_FIELDS:
            res.error(f"{path}.source_field", f"Invalid source_field '{sensor['source_field']}'. Must be one of {sorted(list(VALID_SOURCE_FIELDS))}")

    decode = sensor.get("decode")
    if decode:
        validate_decode(decode, f"{path}.decode", res)
        d_offset = decode.get("offset", 0)
        d_len = decode.get("length", 1)
        required = d_offset + d_len
        min_len = sensor.get("min_length")
        exact_len = sensor.get("length")
        if min_len is not None and required > min_len:
            res.error(f"{path}.decode", f"decode(offset={d_offset} + length={d_len}={required}) exceeds min_length={min_len}")
        if exact_len is not None and required > exact_len:
            res.error(f"{path}.decode", f"decode(offset={d_offset} + length={d_len}={required}) exceeds length={exact_len}")

    if device_source == "obd":
        if sensor.get("pid") is None and sensor.get("preset") is None:
            res.error(f"{path}", "OBD sensor requires 'pid' or 'preset'")
    elif device_source in {"advertisement", "gatt_notify"}:
        if decode is None and platform != "binary_sensor":
            res.warning(f"{path}.decode", "No decode config — sensor will never produce a value")

    if "publish" in sensor:
        validate_publish(sensor["publish"], f"{path}.publish", res)


def validate_control(control: Any, device_source: str, gatt: Optional[dict], obd: Optional[dict], path: str, res: ValidationResult):
    if not isinstance(control, dict):
        res.error(path, "Control must be an object")
        return
    check_unknown_keys(control, KNOWN_CONTROL_KEYS, path, res)
    
    key = control.get("key")
    if not key or not isinstance(key, str):
        res.error(f"{path}.key", "Missing or invalid control 'key'")
        return

    ctype_str = str(control.get("type", ""))
    if ctype_str not in VALID_CONTROL_TYPES:
        res.error(f"{path}.type", f"Invalid control type '{ctype_str}'. Must be one of {sorted(list(VALID_CONTROL_TYPES))}")
        return

    if device_source == "gatt_notify":
        if not gatt or not gatt.get("write_char_uuid"):
            res.error(f"{path}", "Control requires write_char_uuid in gatt config")
    elif device_source == "obd":
        if not obd or not obd.get("tx_char_uuid"):
            res.error(f"{path}", "Control requires tx_char_uuid in obd config")

    cmd_raw = control.get("command", {})
    if not isinstance(cmd_raw, dict):
        res.error(f"{path}.command", "command must be a map of {state: hex_string}")
        return

    # Normalize YAML boolean keys (e.g. on -> True, off -> False in YAML 1.1)
    cmd = {}
    for k, v in cmd_raw.items():
        if k is True:
            cmd["on"] = v
        elif k is False:
            cmd["off"] = v
        else:
            cmd[str(k)] = v

    if ctype_str == "switch":
        for k in ["on", "off"]:
            if k not in cmd:
                res.error(f"{path}.command", f"Switch control missing command key '{k}'")
    elif ctype_str == "button":
        if "press" not in cmd:
            res.error(f"{path}.command", "Button control missing command key 'press'")
    elif ctype_str == "number":
        if "template" not in cmd:
            res.error(f"{path}.command", "Number control missing command key 'template'")
    elif ctype_str == "select":
        options = control.get("options", [])
        if not isinstance(options, list) or not options:
            res.error(f"{path}.options", "Select control requires a non-empty 'options' list")
        else:
            for opt in options:
                if opt not in cmd:
                    res.error(f"{path}.command", f"Select control missing command key for option '{opt}'")


def validate_device(device: Any, path: str, res: ValidationResult):
    if not isinstance(device, dict):
        res.error(path, "Device must be an object")
        return
    check_unknown_keys(device, KNOWN_DEVICE_KEYS, path, res)

    dev_id = device.get("id")
    if not dev_id or not isinstance(dev_id, str):
        res.error(f"{path}.id", "Device missing required 'id'")
    dev_name = device.get("name")
    if not dev_name or not isinstance(dev_name, str):
        res.error(f"{path}.name", "Device missing required 'name'")

    source = str(device.get("source", ""))
    if source not in VALID_SOURCES:
        res.error(f"{path}.source", f"Invalid source '{source}'. Must be one of {sorted(list(VALID_SOURCES))}")
        return

    instance_mode = device.get("instance_mode", "mac")
    if instance_mode not in VALID_INSTANCE_MODES:
        res.error(f"{path}.instance_mode", f"Invalid instance_mode '{instance_mode}'. Must be one of {sorted(list(VALID_INSTANCE_MODES))}")

    match = device.get("match")
    if match:
        if not isinstance(match, dict):
            res.error(f"{path}.match", "match must be an object")
        else:
            check_unknown_keys(match, KNOWN_MATCH_KEYS, f"{path}.match", res)
            if "manufacturer_id" in match:
                m_id = match["manufacturer_id"]
                if not isinstance(m_id, int):
                    res.error(f"{path}.match.manufacturer_id", f"manufacturer_id must be a decimal integer (got '{m_id}')")

    gatt = device.get("gatt")
    if gatt:
        if not isinstance(gatt, dict):
            res.error(f"{path}.gatt", "gatt must be an object")
        else:
            check_unknown_keys(gatt, KNOWN_GATT_KEYS, f"{path}.gatt", res)
            if source == "gatt_notify":
                if not gatt.get("service_uuid"):
                    res.error(f"{path}.gatt.service_uuid", "Missing required 'service_uuid'")
                if not gatt.get("notify_char_uuid"):
                    res.error(f"{path}.gatt.notify_char_uuid", "Missing required 'notify_char_uuid'")

    obd = device.get("obd")
    if obd:
        if not isinstance(obd, dict):
            res.error(f"{path}.obd", "obd must be an object")
        else:
            check_unknown_keys(obd, KNOWN_OBD_KEYS, f"{path}.obd", res)

    sensors = device.get("sensors", [])
    if not isinstance(sensors, list):
        res.error(f"{path}.sensors", "sensors must be a list")
    else:
        for idx, s in enumerate(sensors):
            validate_sensor(s, source, f"{path}.sensors[{idx}]", res)

    controls = device.get("controls", [])
    if not isinstance(controls, list):
        res.error(f"{path}.controls", "controls must be a list")
    else:
        for idx, c in enumerate(controls):
            validate_control(c, source, gatt, obd, f"{path}.controls[{idx}]", res)

    if "publish" in device:
        validate_publish(device["publish"], f"{path}.publish", res)


def validate_config_file(filepath: str) -> ValidationResult:
    res = ValidationResult(os.path.basename(filepath))
    if not os.path.exists(filepath):
        res.error("", f"File '{filepath}' does not exist")
        return res

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        res.error("", f"YAML syntax error: {e}")
        return res

    if not isinstance(data, dict):
        res.error("", "Root must be a YAML mapping")
        return res

    version = data.get("version")
    if version != 1:
        res.warning("version", f"Schema version is {version}, expected 1")

    if "defaults" in data:
        defaults = data["defaults"]
        if not isinstance(defaults, dict):
            res.error("defaults", "defaults must be an object")
        elif "publish" in defaults:
            validate_publish(defaults["publish"], "defaults.publish", res)

    devices = data.get("devices", [])
    if not isinstance(devices, list):
        res.error("devices", "devices must be a list")
    else:
        for idx, dev in enumerate(devices):
            validate_device(dev, f"devices[{idx}]", res)

    return res


def validate_templates_file(filepath: str) -> ValidationResult:
    res = ValidationResult(os.path.basename(filepath))
    if not os.path.exists(filepath):
        res.error("", f"File '{filepath}' does not exist")
        return res

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        res.error("", f"YAML syntax error: {e}")
        return res

    if not isinstance(data, dict):
        res.error("", "Root must be a YAML mapping")
        return res

    templates = data.get("templates")
    if not isinstance(templates, list):
        res.error("templates", "templates must be a list")
        return res

    for idx, t in enumerate(templates):
        path = f"templates[{idx}]"
        if not isinstance(t, dict):
            res.error(path, "Template item must be an object")
            continue
        for key in ["id", "name"]:
            if not t.get(key) or not isinstance(t[key], str):
                res.error(f"{path}.{key}", f"Missing or invalid template '{key}'")
        
        device = t.get("device")
        if not device:
            res.error(f"{path}.device", "Missing 'device' configuration in template")
        else:
            validate_device(device, f"{path}.device", res)

    return res


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(repo_root, "config.yaml")
    templates_file = os.path.join(repo_root, "templates.yaml")

    results = [
        validate_config_file(config_file),
        validate_templates_file(templates_file),
    ]

    total_errors = 0
    total_warnings = 0

    for r in results:
        for w in r.warnings:
            print(f"⚠️  {w}")
            total_warnings += 1
        for e in r.errors:
            print(f"❌ {e}")
            total_errors += 1

    if total_errors == 0:
        print(f"✅ All YAML configurations valid ({total_warnings} warnings, 0 errors).")
        sys.exit(0)
    else:
        print(f"\n💥 Validation failed with {total_errors} errors and {total_warnings} warnings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
