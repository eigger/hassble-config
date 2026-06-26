# HassBle 차량 설정 및 PID 기여 가이드

**[English Version → CONTRIBUTING.md](CONTRIBUTING.md)**

HassBle는 커뮤니티 기반의 오픈소스 프로젝트로, 사용자들이 직접 성공적으로 연동한 OBD-II PID 설정과 BLE 기기 설정을 공유하며 함께 발전해 나갑니다.

본인의 차량에 맞는 PID 설정을 구축하셨다면, 아래 방법 중 편한 방식을 선택해 다른 사용자들을 위해 공유해 주세요! 차량의 설정을 공유하면 동일한 차종을 소유한 다른 사용자들이 단 몇 초 만에 설정을 완료할 수 있습니다.

---

## 🚀 기여 방법

GitHub 사용 방식이나 YAML 파일 편집에 익숙한 정도에 따라 아래 두 가지 방법 중 하나를 선택하실 수 있습니다:

### 방법 A: GitHub Issue로 제보하기 (가장 쉬운 방법)
Git이나 YAML 형식 작성이 익숙하지 않으시다면, 아래 정보를 포함하여 이슈(Issue)로 제보해 주세요. 관리자가 확인 후 검증하여 대신 `templates.yaml`에 반영해 드립니다.
1. **차량 정보**: 제조사, 모델명, 연식, 유종/엔진 형식 (예: *2022년식 현대 아이오닉 5 EV*, *2020년식 쉐보레 콜로라도 2.8L 디젤*).
2. **OBD-II 어댑터**: 사용 중인 어댑터 모델 (예: *vLinker MC+*, *ELM327 v1.5*).
3. **OBD 프로토콜 / 초기화 명령어 (선택)**: 예) CAN 11bit 500kbps의 경우 `ATSP6` 등.
4. **센서 목록**: 각 센서마다 다음 정보를 적어주세요:
   * **센서 이름 및 설명** (예: 엔진오일 온도)
   * **Mode & PID** (예: Mode `22`, PID `1008`)
   * **변환 수식 (Formula)** (예: 수신 바이트 계산식 `a - 40`)
   * **측정 단위** (예: `°C`)
   * **폴링 주기** (예: `10s` 마다)

### 방법 B: Pull Request (PR)로 직접 등록하기 (개발자 권장)
GitHub 사용이 익숙하시다면 이 저장소의 [templates.yaml](templates.yaml) 파일에 본인의 차량 템플릿 설정을 직접 추가하고 Pull Request를 보내주세요. (PR 생성 시 한국어 템플릿을 선택하거나, URL 뒤에 `?template=pull_request_template_ko.md`를 붙여 작성하실 수 있습니다.)

---

## 📝 `templates.yaml` 작성법 및 예시

`templates.yaml`에 차종별 설정을 추가할 때는 아래 예시와 같은 형식을 사용합니다.

각 설정 필드에 대한 상세한 설명과 스펙은 이 저장소의 **[README.ko.md](README.ko.md)** 파일에 매우 상세하게 설명되어 있으니 참고해 주세요.

### 차량 템플릿 작성 예시

```yaml
  - id: obd_hyundai_avante_cn7
    name: "Hyundai Elantra/Avante CN7 (Gasoline)"
    description: "아반떼 CN7 가솔린 모델을 위한 기본 주행 데이터 및 엔진/미션오일 온도 센서 세트"
    device:
      id: avante_cn7_obd
      name: "Avante CN7 OBD"
      source: obd
      obd:
        service_uuid: "18F0"      # OBD-II 어댑터의 BLE 서비스 UUID (대개 FFF0 또는 18F0)
        tx_char_uuid: "2AF1"      # 쓰기(Write) 캐릭터리스틱 UUID
        rx_char_uuid: "2AF0"      # 알림(Notify) 캐릭터리스틱 UUID
        tx_delay: 50ms            # 명령 간 전송 딜레이
        init_commands: ["ATSP6"] # OBD 초기화 명령 (ATSP6 또는 ATSP0 등)
      sensors:
        # 1. 내장 프리셋 사용 (앱에 내장된 공통 PID 정의 활용)
        - { key: rpm, preset: rpm, update_interval: 2s }
        - { key: speed, preset: speed, update_interval: 2s }
        - { key: coolant_temp, preset: coolant_temp, update_interval: 10s }
        
        # 2. 제조사 전용 확장 PID 수동 정의 (프리셋이 없는 경우)
        - key: engine_oil_temp
          mode: "22"             # UDS Mode 22 (확장 PID 읽기)
          pid: "1008"            # 4자리 PID Hex 코드
          formula: "a - 40"      # 'a'는 수신된 첫 번째 바이트. 섭씨 온도로 변환하는 수식
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

### 💡 디코딩 수식(Formula) 작성 팁:
* **바이트 변수**: 응답 바이트 순서대로 `a`, `b`, `c`, `d` 등을 변수로 사용합니다.
* **수학 연산**: `+`, `-`, `*`, `/` 및 괄호 `()`를 사용해 수식을 구성할 수 있습니다. (예: 2바이트 조합 고해상도 값은 `(a*256+b)*0.1` 형식으로 많이 사용됩니다.)

---

## 🤝 도움이 필요하신가요?
다른 앱(Torque Pro, Car Scanner 등)을 통해 본인 차량의 PID와 수식은 알아냈으나, 이를 HassBle의 YAML 스키마 형식으로 변환하기 어려우시다면 주저하지 말고 Q&A Discussion이나 Issue에 질문을 올려주세요. 커뮤니티가 기꺼이 변환 작성을 도와드립니다!

소중한 기여를 통해 모두가 더 편하게 차량 상태를 통합할 수 있도록 도와주셔서 감사합니다! 🚗💨
