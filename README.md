# HassBle Configurations

This repository stores custom device configurations and decoding rules for the **HassBle** Android application.

## How It Works

1. **Configure Devices**: Define the BLE advertisement scanners, active GATT connections, and OBD polling properties inside [config.yaml](config.yaml).
2. **Commit & Push**: Push this repository to GitHub (or any Git platform).
3. **Register in the App**: In the HassBle Android app settings, enter the **Raw URL** of your `config.yaml` file.
   - Example: `https://raw.githubusercontent.com/eigger/hassble-config/main/config.yaml`
4. **Select & Start**: The app automatically fetches the file, parses the configurations, and presents them in the UI. Turn on the sensors you want to declare them in Home Assistant.

## Configuration Schema

The YAML configuration structure supports:

- **`defaults`**: Default value filters (like `on_change_only` or `min_interval` throttle times) shared across devices.
- **`devices`**: List of devices to scan or connect to.
  - **`source: advertisement`**: Passive advertisement listeners. Decodes custom service data or manufacturer data bytes.
  - **`source: obd`**: Active OBD polling plans (rpm, speed, GM extensions, etc.).
  - **`source: gatt_notify`**: Bi-directional active GATT notifier and switch controls.

Refer to the main [HassBle CONFIG_SCHEMA.md](https://github.com/eigger/hassble-android/blob/main/docs/CONFIG_SCHEMA.md) for full configuration specs.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.
