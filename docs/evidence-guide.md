# 제출용 실제 화면 캡처 안내

## Colab 5장

노트북 이름과 Colab 화면임을 알아볼 수 있게 촬영합니다. 코드 입력 화면만 촬영하지 말고 실행 결과를 포함합니다. 코드를 접으면 출력과 그래프를 크게 담을 수 있습니다.

1. `01_gpu.png`: EVIDENCE 01 출력, 실제 GPU 이름, CUDA tensor device
2. `02_data.png`: 학습/검증/테스트 분할 수치와 손글씨 이미지
3. `03_training.png`: 모델 구조, 모델 device=cuda, 3 epoch 학습 결과
4. `04_evaluation.png`: 실제 테스트 정확도와 혼동행렬
5. `05_visualization.png`: 학습/검증 손실·정확도 곡선 및 예측 이미지

추가 보관: 출력 포함 ipynb, metrics.json, 학습 모델 및 그림 ZIP. 자동 생성된 그림 파일만으로 Colab 화면 캡처를 대체하지 않습니다.

## Codex 5장

Codex 대화 화면에서 직접 촬영합니다. 이 문서나 별도 요약 페이지는 Codex 원본 대화 화면을 대체하지 않습니다.

1. `01_request.png`: 최초 로컬 챗봇 요구사항과 설계도
2. `02_implementation.png`: 실제 Python/HTML 파일 구현 및 변경 내역
3. `03_duckdb.png`: DuckDB 연결·적재 검증 작업의 도구 결과
4. `04_tests.png`: 실제 테스트 실행과 통과 결과
5. `05_delivery.png`: 완성된 앱 또는 최종 납품 메시지와 연결 확인

대화 내용 중 비공개 DB 원문, 이메일, 개인 경로가 나타나면 해당 부분이 없는 구간을 선택하거나 필요한 부분만 잘라 촬영합니다. 내용을 조작하거나 실행되지 않은 결과를 합성하지 않습니다. 공지의 ‘Codex 증빙’ 촬영 방식에 별도 기준이 있으면 교수자 기준을 우선합니다.

## 공개 전 점검

- 제공받은 수업용 DB/CSV/XLSX 및 모델 파일 제외
- 개인 settings.json, logs/, runtime/, .venv/ 제외
- 실제 실행 노트북은 계정 정보·비밀 값이 없는지 검토
- 공개 저장소 URL과 README 재현 명령 확인
- 각 증빙에 해당하는 코드와 결과를 서로 연결
