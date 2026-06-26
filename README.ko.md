# HassBle Config

> 이 저장소는 [HassBle](https://github.com/eigger/hassble-android) Android 앱의 기기 설정 파일(`config.yaml`)을 저장합니다.

**[English Documentation → README.md](README.md) | [기여 가이드 → CONTRIBUTING.ko.md](CONTRIBUTING.ko.md)**

---

## 목차

1. [동작 원리](#동작-원리)
2. [빠른 시작](#빠른-시작)
3. [루트 구조](#루트-구조)
4. [defaults — 발행 규칙](#defaults--발행-규칙)
5. [기기 타입](#기기-타입)
6. [source: advertisement — BLE 수동 스캔](#source-advertisement--ble-수동-스캔)
   - [match — 매칭 조건](#match--매칭-조건)
   - [instance_mode — 엔티티 전략](#instance_mode--엔티티-전략)
7. [source: gatt_notify — GATT 연결](#source-gatt_notify--gatt-연결)
8. [source: obd — ELM327 OBD 폴링](#source-obd--elm327-obd-폴링)
9. [sensors — 센서 설정](#sensors--센서-설정)
   - [decode — 바이너리 디코딩](#decode--바이너리-디코딩)
   - [데이터 타입](#데이터-타입)
10. [controls — HA 제어](#controls--ha-제어)
11. [publish — 센서별 발행 필터](#publish--센서별-발행-필터)
12. [OBD 프리셋 목록](#obd-프리셋-목록)
13. [전체 예제](#전체-예제)
14. [주의사항](#주의사항)
15. [기여하기](#기여하기)

---

## 저장소 파일

| 파일 | 용도 |
|------|------|
| `config.yaml` | 게이트웨이 운영 설정 (실제로 동작하는 기기 목록) |
| `templates.yaml` | 센서 탭 **템플릿 가져오기**용 기기 템플릿 |

앱은 선택한 브랜치의 리포 루트에서 두 파일을 고정 이름으로 불러옵니다 (`owner/repo` + 브랜치).

## 동작 원리

HassBle 앱은 이 저장소에서 `config.yaml`과 `templates.yaml`을 다운로드하고, 정의한 규칙에 따라 BLE 데이터를 디코딩한 뒤, [ws_bridge](https://github.com/eigger/hass-ws-bridge) 통합을 통해 Home Assistant에 자동으로 센서를 등록합니다. 코드 수정 없이 YAML만 편집하면 됩니다.

Raw URL (브랜치 `main`):

- 설정: `https://raw.githubusercontent.com/eigger/hassble-config/main/config.yaml`
- 템플릿: `https://raw.githubusercontent.com/eigger/hassble-config/main/templates.yaml`

```
Android Phone (BLE 스캔)
       │  raw bytes
       ▼
  HassBle 앱  ──── config.yaml (이 저장소) ────▶  디코딩 규칙
       │  디코딩된 값
       ▼
  HA WebSocket API  ─────────────────────────────▶  ws_bridge
       │
       ▼
  Home Assistant 엔티티 (sensor / switch / number / …)
```

---

## 빠른 시작

1. 이 저장소를 자신의 GitHub 계정으로 Fork 또는 복사합니다.
2. `config.yaml`을 편집하여 BLE 기기를 정의합니다. 앱에서 빠르게 추가할 블록은 `templates.yaml`에 넣을 수 있습니다.
3. HassBle 앱 → **Sensors 탭** → `your-username/hassble-config`와 브랜치 `main` 입력 (`config.yaml` + `templates.yaml` 자동 로드).
4. **Gateway 탭**에서 HA URL과 토큰(또는 OAuth 로그인)을 입력하고 게이트웨이를 시작합니다.
5. **Sensors 탭**에서 원하는 센서를 활성화하면 Home Assistant에 나타납니다.

> ⚠️ **HA 자격증명(URL / 토큰)을 이 파일에 절대 저장하지 마세요.**  
> 앱 설정에서만 입력하세요.

---

## 루트 구조

```yaml
version: 1

defaults:
  publish:
    on_change_only: true
    min_interval: 10s

devices:
  - id: ...
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `version` | int | `1` | 스키마 버전. 항상 `1`. |
| `defaults.publish` | object | 아래 참조 | 모든 센서에 적용되는 기본 발행 필터. |
| `devices` | list | `[]` | 기기 설정 목록. |

---

## defaults — 발행 규칙

센서 값을 HA에 얼마나 자주, 어떤 조건에서 전송할지를 제어합니다. 기기별 또는 센서별로 덮어쓸 수 있습니다.

```yaml
defaults:
  publish:
    on_change_only: true   # 값이 변할 때만 전송 (기본: true)
    min_interval: 10s      # 전송 최소 간격 (기본: 10s)
    heartbeat: 5m          # 변화 없어도 이 간격으로 강제 전송 (선택)
    deadband: 0.5          # 이 값 미만의 변화는 무시 (선택, 숫자 센서만)
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `on_change_only` | bool | `true` | 값이 변할 때만 전송. |
| `min_interval` | duration | `10s` | 두 번의 전송 사이 최소 간격. 형식: `500ms`, `30s`, `5m`. |
| `heartbeat` | duration | `null` | 변화 없어도 이 간격으로 강제 전송. |
| `deadband` | float | `null` | 이 값 미만의 변화는 무시 (숫자 센서). |

---

## 기기 타입

`devices`의 각 항목에는 데이터 경로를 선택하는 `source` 필드가 필요합니다.

| `source` | 설명 |
|----------|------|
| `advertisement` | BLE 수동 스캔 — 연결 없이 브로드캐스트 패킷을 읽습니다. |
| `gatt_notify` | GATT 능동 연결 — 기기에 연결하여 알림을 구독합니다. 쓰기 명령을 지원합니다. |
| `obd` | BLE를 통한 ELM327 OBD 어댑터 — PID 명령을 폴링하고 ISO-TP 응답을 파싱합니다. |

**모든 기기 타입에 공통인 필드:**

```yaml
- id: my_device          # 고유 식별자 (소문자, 숫자, _)
  name: "My Device"      # 표시 이름 (HA 기기명)
  source: advertisement  # advertisement | gatt_notify | obd
  publish:               # (선택) 이 기기의 모든 센서에 대한 발행 규칙 덮어쓰기
    on_change_only: true
    min_interval: 5s
  sensors: [...]
  controls: [...]        # gatt_notify / obd만 사용 가능
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | string | ✅ | 고유 식별자. HA 엔티티 unique_id에 사용됩니다. 소문자, 숫자, `_` 사용. |
| `name` | string | ✅ | HA 기기에 표시되는 이름. |
| `source` | enum | ✅ | 데이터 소스 타입 (위 참조). |
| `publish` | object | ❌ | 기기 수준의 발행 규칙 덮어쓰기. |
| `sensors` | list | ❌ | 센서 정의 목록. |
| `controls` | list | ❌ | 제어 정의 목록. |

---

## source: advertisement — BLE 수동 스캔

연결 없이 BLE 광고 패킷을 수신합니다. `match`를 사용하여 패킷을 필터링합니다.

```yaml
- id: my_sensor
  name: "My BLE Sensor"
  source: advertisement
  instance_mode: mac      # mac | shared (아래 참조)
  match:
    manufacturer_id: 76   # Apple = 76 (0x004C) — 반드시 10진수 사용
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

### match — 매칭 조건

지정된 모든 조건이 동시에 만족되어야 합니다 (AND 논리). 지정하지 않은 필드는 무시됩니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `mac` | string | 고정 MAC 주소 필터. 형식: `"AA:BB:CC:DD:EE:FF"`. |
| `service_data_uuid` | string | 16비트 또는 128비트 서비스 UUID 접미사. 예: `"F51C"`, `"181A"`. |
| `manufacturer_id` | int | 제조사 company ID. **반드시 10진수 사용** (`0x...` 불가). 예: Apple=`76`. |
| `manufacturer_hex_prefix` | string | 제조사 페이로드(hex 문자열)가 이 접두사로 시작해야 합니다. 예: iBeacon=`"0215"`. |
| `manufacturer_min_length` | int | 제조사 페이로드의 최소 바이트 길이. |
| `name_prefix` | string | BLE 기기 이름이 이 문자열로 시작해야 합니다. |

> **⚠️ Hex 리터럴 주의**  
> YAML 파서(`kaml`)는 `0x...` hex 값을 잘못 파싱할 수 있습니다. 항상 **10진수 정수**를 사용하세요.  
> `0x004C` → `76`, `0x035D` → `861`

### instance_mode — 엔티티 전략

같은 타입의 기기가 여러 개 감지될 때 HA 엔티티를 어떻게 생성할지를 결정합니다.

| 값 | 설명 |
|----|------|
| `mac` (기본) | 고유 MAC 주소마다 별도의 HA 엔티티 세트를 생성합니다. 엔티티 unique_id: `{device_id}_{MAC}_temperature` 등. 앱의 Sensors 탭에서 MAC을 바인딩하면 기기가 스캔되기 전에 엔티티를 미리 생성할 수 있습니다. |
| `shared` | 모든 매칭 광고 기기가 하나의 HA 엔티티를 공유합니다. 마지막으로 수신된 패킷이 상태를 덮어씁니다. 주차 비콘, 클리커 등에 유용합니다. |

---

## source: gatt_notify — GATT 연결

특정 BLE 기기에 연결하여 GATT 캐릭터리스틱을 구독하고 알림을 수신합니다. 선택적으로 hex 명령을 역방향으로 전송할 수 있습니다.

```yaml
- id: custom_meter
  name: "Custom BLE Meter"
  source: gatt_notify
  gatt:
    mac: "AA:BB:CC:DD:EE:FF"   # 또는 앱 Sensors 탭에서 바인딩
    service_uuid: "ffe0"
    notify_char_uuid: "ffe1"
    write_char_uuid: "ffe2"    # 선택 — controls 사용 시 필요
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

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `mac` | string | ❌ | 기기 MAC 주소. 앱 바인딩으로도 설정 가능. |
| `service_uuid` | string | ✅ | GATT 서비스 UUID (16비트 또는 128비트). |
| `notify_char_uuid` | string | ✅ | 알림을 구독할 캐릭터리스틱. |
| `write_char_uuid` | string | ❌ | 명령을 전송할 캐릭터리스틱 (controls에 필요). |
| `auto_connect` | bool | ❌ | 연결 끊김 시 자동 재연결. 기본 `true`. |

> YAML에 `mac`을 설정하지 않으면 앱의 **Sensors 탭**에서 기기 옆 "Connect / Bind"를 눌러 바인딩하세요.

---

## source: obd — ELM327 OBD 폴링

BLE ELM327 어댑터에 연결하여 OBD-II(및 GM mode 22) PID 명령을 전송하고 ISO-TP 응답을 파싱합니다. 내장 `preset`을 사용하거나 `mode`/`pid`/`formula`를 직접 정의할 수 있습니다.

```yaml
- id: car_obd
  name: "Vehicle OBD"
  source: obd
  obd:
    # mac: "AA:BB:CC:DD:EE:FF"  # 또는 앱에서 바인딩
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
      - "ATSP6"     # 프로토콜: ATSP0=자동, ATSP6=ISO 15765-4 CAN 500kbps
  sensors:
    # 프리셋 사용 (권장)
    - { key: rpm,   preset: rpm,   update_interval: 1s }
    - { key: speed, preset: speed, update_interval: 1s }
    # 직접 정의
    - key: custom_pid
      mode: "01"
      pid: "0C"
      formula: "(a*256+b)/4"
      unit: "rpm"
      state_class: measurement
      update_interval: 1s
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `mac` | string | — | 어댑터 MAC. 여기 또는 앱 바인딩으로 설정. |
| `service_uuid` | string | `"FFF0"` | BLE GATT 서비스 UUID. |
| `tx_char_uuid` | string | `"FFF2"` | 쓰기 캐릭터리스틱 (명령 전송). |
| `rx_char_uuid` | string | `"FFF1"` | 알림 캐릭터리스틱 (응답 수신). |
| `tx_delay` | duration | `50ms` | 연속 명령 사이 딜레이. |
| `init_commands` | list | `[]` | 폴링 시작 전 연결마다 한 번 전송하는 초기 명령. |
| `auto_connect` | bool | `true` | 연결 끊김 시 자동 재연결. |

**OBD 센서 전용 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `preset` | string | 내장 프리셋 사용 (아래 표 참조). |
| `mode` | string | OBD 모드. `"01"`=표준, `"22"`=제조사 확장. 기본 `"01"`. |
| `pid` | string | PID hex 코드. 예: `"0C"`, `"199A"`. |
| `formula` | string | 수식. `a`,`b`,`c`,`d`는 응답 바이트. 예: `"(a*256+b)/4"`. |
| `update_interval` | duration | 이 PID를 폴링하는 간격. 기본 `60s`. |
| `pre_commands` | list | 이 PID 전에 전송할 추가 명령 (예: GM 헤더 전환). |

---

## sensors — 센서 설정

`sensors` 목록의 각 항목은 하나의 HA 엔티티를 정의합니다.

```yaml
sensors:
  - key: temperature           # 필수 — 기기 내 고유 키
    platform: sensor           # sensor | binary_sensor | text_sensor
    device_class: temperature  # HA device_class (선택)
    unit: "°C"
    state_class: measurement   # measurement | total | total_increasing
    icon: "mdi:thermometer"
    entity_category: diagnostic # diagnostic | config (일반 센서는 생략)
    accuracy_decimals: 2
    source_field: manufacturer_data  # advertisement만
    min_length: 24
    decode:
      offset: 18
      length: 2
      type: uint16
      endian: big
      scale: 0.002670288
      offset_value: -45
    publish:                   # 이 센서만의 발행 규칙 덮어쓰기
      deadband: 0.1
      min_interval: 30s
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `key` | string | ✅ | 기기 내 고유 키. HA 엔티티 unique_id의 일부. |
| `platform` | string | ❌ | HA 엔티티 플랫폼. 기본 `sensor`. |
| `device_class` | string | ❌ | HA device class (temperature, humidity, battery, voltage, …). |
| `unit` | string | ❌ | HA에 표시되는 단위. |
| `state_class` | string | ❌ | HA 통계용 state class. |
| `icon` | string | ❌ | MDI 아이콘. 예: `"mdi:thermometer"`. |
| `entity_category` | string | ❌ | `diagnostic` 또는 `config`. 일반 센서는 생략. |
| `accuracy_decimals` | int | ❌ | 디코딩된 값을 소수 N자리로 반올림. |
| `source_field` | enum | ❌ | `manufacturer_data` / `service_data` / `raw`. 기본 `raw`. |
| `min_length` | int | ❌ | 페이로드가 N바이트 미만이면 이 센서를 건너뜀. |
| `decode` | object | ❌ | 바이너리 디코딩 규칙. 아래 참조. |
| `publish` | object | ❌ | 이 센서만의 발행 규칙 덮어쓰기. |

### decode — 바이너리 디코딩

raw 바이트 배열에서 숫자 또는 문자열 값을 추출합니다.

**공식:** `최종값 = (raw_정수 * scale) + offset_value`

```yaml
decode:
  offset: 18          # 바이트 오프셋 (0-based)
  length: 2           # 읽을 바이트 수
  type: uint16        # 데이터 타입 (아래 표 참조)
  endian: big         # big | little
  bitmask: 0x0F       # (선택) AND 비트마스크 적용 후 디코딩
  scale: 0.1          # (선택) 곱할 계수. 기본 1.0
  offset_value: -40   # (선택) 더할 오프셋. 기본 0.0
  map:                # (선택) 정수값 → 문자열 매핑
    "0": "off"
    "1": "on"
    "2": "standby"
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `offset` | int | `0` | 시작 바이트 인덱스 (0부터). |
| `length` | int | `1` | 읽을 바이트 수. |
| `type` | enum | `uint8` | 바이트를 해석할 데이터 타입. |
| `endian` | enum | `big` | 바이트 순서. `big`=MSB 먼저, `little`=LSB 먼저. |
| `bitmask` | int | `null` | 스케일링 전 AND 비트마스크 적용. |
| `scale` | float | `1.0` | raw 정수에 곱할 계수. |
| `offset_value` | float | `0.0` | 스케일링 후 더하는 값: `(raw * scale) + offset_value`. |
| `map` | object | `{}` | 정수 결과를 문자열로 매핑. 키는 따옴표로 감싼 문자열. |

### 데이터 타입

| 타입 | 바이트 | 설명 |
|------|--------|------|
| `uint8` | 1 | 부호 없는 8비트 정수 (0–255). |
| `int8` | 1 | 부호 있는 8비트 정수 (-128–127). |
| `uint16` | 2 | 부호 없는 16비트 정수 (0–65535). |
| `int16` | 2 | 부호 있는 16비트 정수 (-32768–32767). |
| `uint32` | 4 | 부호 없는 32비트 정수. |
| `int32` | 4 | 부호 있는 32비트 정수. |
| `float32` | 4 | IEEE 754 단정밀도 부동소수점. |
| `timestamp` | 4 | 각 바이트를 월/일/시/분으로 해석. ISO 8601 문자열 반환. |
| `string` | N | 바이트를 ASCII로 디코딩. `platform: text_sensor`와 함께 사용. |

---

## controls — HA 제어

HA에서 제어 시 BLE 쓰기 명령을 전송하는 HA 엔티티를 정의합니다. `gatt_notify`와 `obd` 소스에서만 사용 가능합니다.

```yaml
controls:
  # Switch — on/off hex 명령
  - key: relay
    type: switch
    name: "Main Relay"
    icon: "mdi:electric-switch"
    entity_category: config
    command:
      on:  "A10100"
      off: "A10000"

  # Number — 값을 hex에 삽입
  - key: brightness
    type: number
    min: 0
    max: 100
    step: 1
    command:
      template: "B2{value:02X}FF"

  # Select — 옵션별 hex 명령
  - key: mode
    type: select
    options: ["auto", "cool", "heat", "fan"]
    command:
      auto: "C000"
      cool: "C001"
      heat: "C002"
      fan:  "C003"

  # Button — 누르면 hex 전송
  - key: restart
    type: button
    command:
      press: "FFFE"
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `key` | string | ✅ | 기기 내 고유 키. |
| `type` | enum | ✅ | `switch` / `number` / `select` / `button`. |
| `name` | string | ❌ | HA 표시 이름. 생략 시 key에서 자동 생성. |
| `icon` | string | ❌ | MDI 아이콘. |
| `entity_category` | string | ❌ | `config` 또는 `diagnostic`. |
| `command` | object | ✅ | 명령 맵. type에 따라 키가 다릅니다 (위 예제 참조). |
| `options` | list | select만 | `select` 타입 옵션 목록. |
| `min` | float | number만 | `number` 타입 최솟값. |
| `max` | float | number만 | `number` 타입 최댓값. |
| `step` | float | ❌ | `number` 타입 단계. |

**command 템플릿 플레이스홀더:**

| 플레이스홀더 | 설명 |
|-------------|------|
| `{value}` | 정수 값 (10진수). |
| `{value:02X}` | 값을 2자리 대문자 hex로 (0 패딩). |
| `{value:04X}` | 4자리 대문자 hex. |

---

## publish — 센서별 발행 필터

특정 센서에 대해 전역 `defaults.publish`를 덮어씁니다. 느리게 변하는 센서(연료량)나 빠른 업데이트가 필요한 센서(RPM)에 유용합니다.

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

**우선순위:** sensor `publish` > device `publish` > `defaults.publish`

---

## OBD 프리셋 목록

OBD 센서에서 `preset: <이름>`으로 내장 정의를 사용합니다. 프리셋 지정 후 개별 필드(`unit`, `accuracy_decimals` 등)를 덮어쓸 수 있습니다.

### 표준 OBD-II (mode 01)

| 프리셋 | PID | 공식 | 단위 | 설명 |
|--------|-----|------|------|------|
| `rpm` | `0C` | `(a*256+b)/4` | rpm | 엔진 RPM |
| `speed` | `0D` | `a` | km/h | 차속 |
| `engine_load` | `04` | `a/2.55` | % | 엔진 부하 |
| `throttle` | `11` | `a/2.55` | % | 스로틀 개도 |
| `coolant_temp` | `05` | `a-40` | °C | 냉각수 온도 |
| `intake_air_temp` | `0F` | `a-40` | °C | 흡기 온도 |
| `ambient_temp` | `46` | `a-40` | °C | 외기 온도 |
| `battery_voltage` | `42` | `(a*256+b)/1000` | V | 배터리 전압 |
| `run_time` | `1F` | `a*256+b` | s | 시동 후 경과 시간 |
| `fuel_level` | `2F` | `a/2.55` | % | 연료량 |
| `actual_torque` | `62` | `a-125` | % | 실제 토크 |
| `odometer` | `A6` | `(a*16777216+b*65536+c*256+d)/10` | km | 주행 거리 |

### GM 확장 (mode 22)

| 프리셋 | PID | 공식 | 단위 | 설명 |
|--------|-----|------|------|------|
| `gm_current_gear` | `199A` | `a` | — | 현재 기어 |
| `gm_prnd_status_alt` | `2889` | `a` | — | PRND 상태 |
| `gm_oil_pressure` | `115C` | `(a*0.65)-17.5` | psi | 오일 압력 |
| `gm_trans_temp` | `1940` | `a-40` | °C | 변속기 온도 |
| `gm_fuel_level_liters` | `132A` | `(a*256+b)/64` | L | 연료량 (리터) |

---

## 전체 예제

### 예제 1 — Jaalee JHT (iBeacon 온도·습도)

```yaml
# instance_mode: mac → 각 기기 MAC마다 별도 엔티티 생성
- id: jaalee_jht
  name: "Jaalee JHT"
  source: advertisement
  instance_mode: mac
  match:
    manufacturer_id: 76          # Apple Inc. (반드시 10진수)
    manufacturer_min_length: 24
    manufacturer_hex_prefix: "0215"   # iBeacon 타입 마커
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

### 예제 2 — 커스텀 서비스 데이터 센서

```yaml
# 서비스 데이터에 센서 값이 포함된 커스텀 기기
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

### 예제 3 — GATT 센서 + 스위치 제어

```yaml
# GATT 기반 전력 모니터 + 릴레이 제어
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

### 예제 4 — OBD 프리셋 + 커스텀 발행 규칙

```yaml
# OBD 차량 센서 (프리셋 + 커스텀 발행 규칙)
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
        deadband: 1.0     # 1% 미만 변화 무시
        min_interval: 60s
        heartbeat: 10m
```

### 예제 5 — 값 매핑 (상태 코드)

```yaml
# 상태 코드를 문자열로 매핑하는 예제
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

## 주의사항

### ⚠️ manufacturer_id는 반드시 10진수로

YAML 파서(`kaml`)는 `0x004C`를 `0`으로 파싱하거나 오류를 낼 수 있습니다. 항상 hex를 10진수로 변환하세요:

```yaml
# ❌ 잘못된 방법 — 파싱 오류 가능
manufacturer_id: 0x004C

# ✅ 올바른 방법
manufacturer_id: 76       # 0x004C = 76
manufacturer_id: 861      # 0x035D = 861
```

### match의 AND 논리

모든 `match` 조건은 AND로 결합됩니다. `service_data_uuid`와 `manufacturer_id`를 함께 지정하면 패킷이 **둘 다** 만족해야 합니다. 기기가 항상 특정 필드를 광고하지 않는다면 해당 조건을 제거하세요.

### instance_mode: mac — 조기 엔티티 생성을 위한 바인딩

`instance_mode: mac`이고 `match.mac`이 없으면 기기가 BLE 스캔에서 감지된 후에야 HA 엔티티가 나타납니다. 게이트웨이 연결 즉시 엔티티가 나타나도록 하려면 앱 **Sensors 탭** → "Connect / Bind"에서 MAC을 바인딩하세요.

### source_field 선택

광고 센서의 페이로드 소스 선택:
- `manufacturer_data` — 제조사 ID 이후 데이터 (커스텀 센서에서 가장 일반적)
- `service_data` — 서비스 데이터 AD 타입 데이터 (0x181A 등 표준 프로필에 일반적)
- `raw` — 전체 스캔 레코드 바이트 (거의 사용 안 함)

### 시간 형식

시간은 밀리초(`ms`), 초(`s`), 분(`m`)을 지원합니다.

```yaml
tx_delay: 50ms
min_interval: 10s
heartbeat: 5m
update_interval: 1s
```

### 설정은 캐시됨

앱은 마지막으로 성공적으로 불러온 설정을 캐시합니다. 시작 시 네트워크가 없으면 캐시를 사용합니다. 이 경우 앱 상단에 "캐시된 설정 사용 중"이 표시됩니다.

---

## 기여하기

본인 차량의 OBD-II PID 설정을 공유해 주시면 다른 사용자들에게 큰 도움이 됩니다! 자세한 공유 및 기여 방법은 [기여 가이드(CONTRIBUTING.ko.md)](CONTRIBUTING.ko.md)를 참고해 주세요.

---

## 라이선스

MIT
