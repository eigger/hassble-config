---
name: "🚗 Vehicle PID Contribution (English)"
about: Share your vehicle's working OBD-II PID configuration.
title: "[Vehicle] Manufacturer Model (Year)"
labels: vehicle-config
assignees: ''
---

### 1. Vehicle Information
* **Manufacturer**: 
* **Model**: 
* **Year**: 
* **Engine/Fuel Type**: (e.g., Gasoline, Diesel, Hybrid, EV)

### 2. Connection Settings
* **OBD-II Adapter Model**: (e.g., vLinker MC+, ELM327 v1.5)
* **OBD Protocol / Init Commands (If any)**: (e.g., `ATSP6`, `ATSP0` or leave blank if standard)

### 3. Sensor List
Please list the OBD PIDs you successfully configured.

| Sensor Name | Mode | PID | Formula (Decoding) | Unit | Description | Update Interval |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *e.g., Engine Oil Temp* | *22* | *1008* | *a - 40* | *°C* | *Engine oil temperature* | *10s* |
| | | | | | | |
| | | | | | | |

*Note: In the formula, use `a`, `b`, `c`, `d`, etc., for response bytes.*

### 4. Raw YAML Draft (Optional)
If you have already generated a YAML config draft in the app or wrote one yourself, paste it here:

```yaml
# Paste your YAML snippet here if available
```

### 5. Verification
* [ ] I have successfully tested these PIDs in my car using the HassBle app.
* Additional comments or screenshots:
