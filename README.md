# Running Newsletter Operations

국내 일반 러너를 위한 화/목/토 오전 8시 러닝 뉴스레터 운영 키트입니다.

목표는 최신 러닝 소식을 사람이 직접 수집·검수한 뒤, 이메일과 웹사이트에 바로 발행할 수 있는 짧은 뉴스레터를 자동 생성하는 것입니다.

## 운영 원칙

- 독자: 국내 일반 러너
- 발행 주기: 주 3회, 화/목/토 오전 8시(KST)
- 회차 구성: 5개 소식, 기본 비중은 국내 3개 + 해외 2개
- 톤: 친근한 큐레이터
- 제작 방식: 반자동. 수집·선별·팩트체크는 사람이 하고, 원고·이미지·웹 데이터·메일 발송은 스크립트가 처리합니다.

## 폴더 구조

- `docs/editorial-guidelines.md`: 선별 기준, 톤, 저작권·검수 기준, 1차/2차 검수 체크리스트, 소식 구조
- `data/candidates.csv`: 최신 회차 생성용 후보 소식 파일
- `data/candidates_archive.csv`: 모든 회차 후보 소식 누적 기록
- `issues/`: 회차별 뉴스레터 원고(md) 저장 위치
- `web/public/assets/issues/YYYY-MM-DD/`: 회차별 메일/웹 공용 이미지 저장 위치 (단일 출처)
- `scripts/run_newsletter_pipeline.py`: 후보 검증부터 원고·이미지·웹 데이터 생성과 선택적 메일 발송까지 실행하는 표준 파이프라인
- `scripts/generate_issue.py`: 후보 CSV에서 뉴스레터 초안을 생성하는 스크립트
- `scripts/generate_newsletter_art.py`: 회차별 메일/웹용 이미지를 생성하는 스크립트
- `scripts/generate_web_data.py`: 뉴스레터 원고를 웹사이트 데이터(JSON)로 변환하는 스크립트
- `web/`: 러너리 뉴스레터 웹사이트

## 빠른 시작

1. 최근 러닝 소식을 직접 조사해 `data/candidates_archive.csv`에 새 `issue_id`로 이번 회차 후보 소식 5개를 추가합니다.
   `issue_date`는 실제 발행일, `verification_status`는 검수 완료 후 `reviewed`로 둡니다.
2. 아래 명령으로 최신 회차를 `data/candidates.csv`로 내보냅니다.

```bash
python3 scripts/export_latest_candidates.py
```

3. `selected` 값을 `yes`로 표시한 소식 5개를 확인합니다.
4. 아래 명령으로 초안을 생성합니다.

```bash
python3 scripts/generate_issue.py
```

5. 메일/웹용 이미지를 생성합니다. 기본 Python에 Pillow가 없다면 `python3 -m pip install Pillow`를 먼저 실행합니다.

```bash
python3 scripts/generate_newsletter_art.py
```

6. 러너리 웹사이트용 데이터를 생성합니다.

```bash
python3 scripts/generate_web_data.py
```

기본 출력 파일:

- `web/src/data/issues.json`: 웹앱이 읽는 회차 데이터

7. 웹사이트를 로컬에서 확인합니다.

```bash
cd web
npm install
npm run dev
```

배포용 빌드는 아래 명령을 사용합니다. 빌드 전에 웹사이트 데이터가 자동으로 다시 생성됩니다.

```bash
cd web
npm run build
```

8. 생성된 `issues/YYYY-MM-DD-running-newsletter.md`, `web/public/assets/issues/YYYY-MM-DD/`, `web/`을 열어 사람이 최종 검수합니다.
9. SMTP 환경변수와 `RUNEORRRI_SITE_BASE_URL`을 설정했다면 메일을 보냅니다.

```bash
python3 scripts/send_issue_email.py
```

메일 발송 전 `scripts/send_issue_email.py`는 웹사이트 데이터를 다시 생성하고, 메일 상단 `@runeorrri`, 제목, 히어로 이미지를 `RUNEORRRI_SITE_BASE_URL/NN`(회차 번호)로 연결합니다.

뉴스레터 원고는 이메일 본문 텍스트와 웹사이트 데이터의 원천으로 사용하고, `web/public/assets/issues/YYYY-MM-DD/` 이미지는 메일 인라인 이미지와 웹사이트 대표 이미지로 함께 사용합니다.

## 표준 자동화 파이프라인

아래 명령 하나가 발행 전 후보 검증, 원고 생성, 메일/웹 이미지 생성, 웹 데이터 생성을 순서대로 실행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id today --no-email
```

메일까지 보내려면 `.env` 설정 후 아래처럼 실행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id today --send-email
```

`--issue-id today`는 `data/candidates_archive.csv`에서 오늘 날짜(`issue_date`)의 후보를 찾습니다. 오늘 후보가 없거나 선택된 후보가 5개가 아니거나 검수가 끝나지 않았으면 발송하지 않고 실패합니다.

## 자동 발송 설정

GitHub Actions 워크플로 `.github/workflows/newsletter.yml`이 화/목/토 오전 8시(KST)에 실행됩니다. 자동 수집과 AI 보강은 실행하지 않고, 미리 준비된 `reviewed` 후보 5개로 원고·이미지·웹 데이터·메일 발송만 진행합니다.

실제 이메일 발송까지 하려면 `.env.example`을 참고해 `.env` 파일에 SMTP 설정과 수신 주소를 넣습니다.

## 발행 전 필수 체크

- 모든 소식에 원문 링크가 있는가?
- 대회, 접수, 제품명, 가격, 날짜를 공식 출처로 확인했는가?
- 해외 소식에 한국 러너에게 필요한 맥락을 붙였는가?
- 보도자료성 콘텐츠를 광고처럼 쓰지 않았는가?
- 저장 또는 공유를 유도할 만한 소식이 최소 1개 있는가?

## 발행 후 확인

- 최신 회차가 `/NN` 경로로 열리는지 확인합니다.
- 메일을 보냈다면 히어로·라인업·체크포인트 이미지가 모두 표시되고 상단 링크가 해당 회차로 연결되는지 확인합니다.
