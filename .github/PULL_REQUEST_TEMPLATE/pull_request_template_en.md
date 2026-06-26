## Description
Please describe the vehicle template or configuration changes you are proposing.

- Added/Updated Vehicle: E.g., *Hyundai Avante CN7*
- Source Type: OBD / BLE Advertisement / GATT
- Main Features: E.g., *Added custom Mode 22 PIDs for Oil Temperature and Gear Status*

---

## Checklist
Before submitting this PR, please check the following:

- [ ] **Valid YAML Syntax**: The YAML formatting is correct and contains no parser errors.
- [ ] **No Hex Literals for IDs**: Used decimal integers for numeric parameters like `manufacturer_id` (e.g., Apple is `76`, not `0x004C`).
- [ ] **Unique Template IDs**: The new template ID is unique and doesn't conflict with existing ones in `templates.yaml`.
- [ ] **Tested & Verified**: I have tested this configuration in the HassBle app and verified that the sensor data is decoded properly.

---

## YAML Code Snippet (Optional)
If you've added a new template, you can highlight it below for a quick review:

```yaml
# Put your added template block here
```
