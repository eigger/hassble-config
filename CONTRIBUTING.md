# Contributing to HassBle Configurations

**[한국어 기여 가이드 → CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)**

Welcome! HassBle is a community-driven project, and we love it when users share their working OBD-II PID configurations and BLE device configurations.

By contributing your vehicle's specific PIDs and configurations, you can help other owners of the same car set up their Home Assistant integration in seconds.

---

## 🚀 How to Contribute

Depending on your comfort level with GitHub and YAML, you can choose one of the following methods:

### Option A: Open a GitHub Issue (Easiest)
If you are not familiar with Git or YAML editing, simply open an issue with the following details:
1. **Vehicle Info**: Manufacturer, Model, Year, and Engine/Fuel Type (e.g., *2022 Hyundai Ioniq 5 EV*, *2020 Chevrolet Colorado 2.8L Diesel*).
2. **OBD-II Adapter**: The adapter you are using (e.g., *vLinker MC+*, *ELM327 v1.5*).
3. **OBD Protocol / Init Commands (If any)**: E.g., `ATSP6` for ISO 15765-4 CAN (11bit/500kbps).
4. **Sensor List**: For each sensor, please provide:
   * **Name/Description** (e.g., Engine Oil Temperature)
   * **Mode & PID** (e.g., Mode `22`, PID `1008`)
   * **Formula** (e.g., `a - 40` to decode bytes)
   * **Unit of Measurement** (e.g., `°C`)
   * **Polling Interval** (e.g., every `10s`)

We will verify your submission and manually add it to the global `templates.yaml` list!

### Option B: Submit a Pull Request (PR) (For Developers)
If you are comfortable with Git, you can directly add your vehicle configuration to [templates.yaml](templates.yaml) and submit a Pull Request. (You can select the English template when creating the PR, or append `?template=pull_request_template_en.md` to the PR creation URL.)

---

## 📝 How to Format Your Template in `templates.yaml`

When adding a new vehicle template to `templates.yaml`, please follow the structure below. 

For detailed information about the parameters, please refer to the [README.md](README.md) file in this repository.

### Template Schema Example

```yaml
  - id: obd_hyundai_avante_cn7
    name: "Hyundai Elantra/Avante CN7 (Gasoline)"
    description: "Standard driving metrics plus engine/transmission oil temperature sensors."
    device:
      id: avante_cn7_obd
      name: "Avante CN7 OBD"
      source: obd
      obd:
        service_uuid: "18F0"      # Ble service UUID of your OBD-II adapter (typically FFF0 or 18F0)
        tx_char_uuid: "2AF1"      # Write characteristic UUID
        rx_char_uuid: "2AF0"      # Notify characteristic UUID
        tx_delay: 50ms            # Delay between sending commands
        init_commands: ["ATSP6"] # OBD initialization commands (often ATSP6 or ATSP0)
      sensors:
        # 1. Standard Presets (Using pre-defined presets in the app)
        - { key: rpm, preset: rpm, update_interval: 2s }
        - { key: speed, preset: speed, update_interval: 2s }
        - { key: coolant_temp, preset: coolant_temp, update_interval: 10s }
        
        # 2. Custom Manufacturer-Specific UDS PIDs (Without presets)
        - key: engine_oil_temp
          mode: "22"             # UDS mode 22 (Extended PIDs)
          pid: "1008"            # 4-digit PID for Mode 22
          formula: "a - 40"      # 'a' is the first response byte. Decodes the OBD reply to Celsius.
          unit: "°C"
          device_class: temperature
          state_class: measurement
          update_interval: 10s
          
        - key: trans_oil_temp
          mode: "22"
          pid: "2201"
          formula: "a - 40"
          unit: "°C"
          device_class: temperature
          state_class: measurement
          update_interval: 10s
```

### 💡 Tips for Writing Formulas:
* **Byte Variables**: Use `a`, `b`, `c`, `d`, etc., to represent sequential bytes returned from the OBD-II response.
* **Math Operations**: Standard operations like `+`, `-`, `*`, `/`, and parentheses `()` are fully supported. (e.g., `(a*256+b)*0.1` is a common formula for reading high-resolution values).

---

## 🤝 Need Help?
If you've managed to read some PIDs using other OBD apps (like Torque Pro or Car Scanner) but aren't sure how to translate the formulas and PIDs into HassBle's YAML schema, feel free to open a Q&A Discussion or an Issue. The community is happy to help you format the YAML configurations!

Thank you for contributing and helping make HassBle better for everyone! 🚗💨
