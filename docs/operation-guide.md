# 운영 가이드

## 1. 오전 후보 수집

최근 48~72시간 안에 나온 국내외 러닝 소식을 모읍니다. 속보성보다 일반 러너에게 쓸모 있는 정보를 우선합니다.

권장 수집 카테고리:

- 오늘의 러닝 뉴스
- 대회, 접수, 이벤트
- 장비, 브랜드, 기어
- 해외 트렌드 또는 엘리트 러닝

자동 수집은 Google News RSS 검색 피드 기반으로 실행합니다.

```bash
python3 scripts/collect_running_news.py --dry-run
python3 scripts/collect_running_news.py
```

수집 쿼리는 `data/collection_queries.csv`에서 관리합니다. 자동 수집 후보는 `verification_status=auto_collected`로 저장됩니다. 사람이 직접 검수한 뒤 발행하려면 `verification_status`를 `reviewed`로 바꿉니다.

## 2. 1차 필터

다음 질문에 하나라도 명확히 답할 수 있는 소식을 우선합니다.

- 독자가 참가할 수 있는가?
- 독자가 구매나 장비 선택에 참고할 수 있는가?
- 훈련, 건강, 커뮤니티 활동에 바로 도움이 되는가?
- 국내 러닝 문화 흐름을 보여주는가?
- 해외 소식이라면 한국 러너에게 전달할 이유가 있는가?

## 3. 2차 검수

발행 전 반드시 확인합니다.

- 날짜: 기사 발행일과 실제 이벤트 날짜가 맞는지 확인
- 출처: 대회·접수 정보는 공식 홈페이지 또는 공식 SNS 우선
- 숫자: 참가비, 거리, 기록, 인원, 판매가 등 재확인
- 맥락: 보도자료는 브랜드 주장과 러너에게 실제로 유용한 정보를 분리
- 링크: 독자가 바로 확인할 수 있는 원문 URL 포함

## 4. 초안 생성

`selected` 값을 `yes`로 표시한 소식 5개를 기준으로 표준 파이프라인을 실행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id today --no-email
```

자동 수집 후보까지 허용하려면 아래처럼 실행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --collect --allow-auto-collected --no-email
```

기본 출력 파일:

- `issues/YYYY-MM-DD-running-newsletter.md`
- `issues/YYYY-MM-DD-art/*.png`
- `web/src/data/issues.json`
- `web/public/assets/issues/YYYY-MM-DD/*.png`

## 5. 최종 편집

각 소식은 아래 구조를 유지합니다.

- 제목 1줄
- 2~3문장 요약
- 러너에게 중요한 이유 1문장
- 원문 링크
- 웹과 메일에 들어갈 한 줄 관점

문장은 짧게 씁니다. “대단하다”보다 “무엇을 확인하면 좋은지”를 말합니다.

## 6. 발행 및 확인

메일 발송까지 진행할 때는 SMTP 환경변수 설정 후 아래 명령을 사용합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id today --send-email
```

완전 자동 수집과 메일 발송을 함께 실행하려면 아래 명령을 사용합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --collect --allow-auto-collected --send-email
```

웹사이트 배포 URL은 `.env`의 `RUNEORRRI_SITE_BASE_URL`에 저장합니다. 예:

```bash
RUNEORRRI_SITE_BASE_URL=https://runeorrri.pages.dev
```

메일 상단의 `@runeorrri`, 제목, 히어로 이미지는 모두 해당 회차 웹페이지로 연결됩니다.

발행 후에는 웹사이트에서 최신 회차가 `/NN`과 `/issues/YYYY-MM-DD` 양쪽 경로로 열리는지 확인합니다. 메일 발송을 한 경우에는 히어로 이미지, 라인업 이미지, 체크포인트 이미지가 모두 보이고 상단 링크가 해당 회차 웹페이지로 연결되는지 확인합니다.
