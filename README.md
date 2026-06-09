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

이 저장소의 Git 루트는 `newsletter/`입니다. Cloudflare Pages나 GitHub Actions의 작업 디렉터리도 이 루트를 기준으로 봅니다.

- `docs/editorial-guidelines.md`: 선별 기준, 톤, 저작권·검수 기준, 1차/2차 검수 체크리스트, 소식 구조
- `data/candidates_archive.csv`: 모든 회차 후보 소식 누적 기록이자 생성 스크립트의 원본
- `issues/`: 회차별 뉴스레터 원고(md) 저장 위치
- `web/public/assets/issues/YYYY-MM-DD/`: 회차별 메일/웹 공용 이미지 저장 위치 (단일 출처)
- `scripts/run_newsletter_pipeline.py`: 후보 검증부터 원고·이미지·웹 데이터 생성까지 실행하는 표준 파이프라인
- `scripts/generate_issue.py`: `issue_id` 기준으로 archive에서 뉴스레터 초안을 생성하는 스크립트
- `scripts/generate_newsletter_art.py`: 회차별 메일/웹용 이미지를 생성하는 스크립트
- `scripts/generate_web_data.py`: 뉴스레터 원고를 웹사이트 데이터(JSON)로 변환하는 스크립트
- `web/`: 러너리 뉴스레터 웹사이트

## 빠른 시작

1. 최근 러닝 소식을 직접 조사해 `data/candidates_archive.csv`에 새 `issue_id`로 이번 회차 후보 소식 10개를 추가합니다.
   `issue_date`는 실제 발행일, `verification_status`는 검수 완료 후 `reviewed`로 둡니다.
   이 10개는 기존 발행호와 주제·대회·브랜드·URL이 겹치면 안 됩니다.
2. 수집 후보 10개를 검증합니다.

```bash
python3 scripts/validate_candidate_pool.py 2026-05-05-05 --mode collect
```

3. `collect` 검증을 통과한 후보 10개를 보여줄 때 에디터 추천 5개도 함께 제안합니다.
   추천은 아직 승인으로 보지 않으며, 이 단계에서는 `selected=no`를 유지합니다.
4. 추천 5개를 보여주기 전 추천 row 번호도 검증합니다.

```bash
python3 scripts/validate_candidate_pool.py 2026-05-05-05 --mode collect --recommend 1,2,5,7,9
```

5. 사용자가 추천안 그대로 진행하거나 10개 중 발행할 5개를 고르면 그 5개만 `selected=yes`로 표시하고 나머지는 `selected=no`로 둡니다.
6. 아래 명령으로 발행 검증, 원고, 이미지, 웹 데이터를 생성합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id 2026-05-05-05
```

기본 출력 파일:

- `web/src/data/issues.json`: 웹앱이 읽는 회차 데이터

7. 웹사이트를 로컬에서 확인합니다.

```bash
npm run dev
```

배포용 빌드는 저장소 루트에서 아래 명령을 사용합니다. 루트 `build` 스크립트가 `web` 의존성을 설치하고, 빌드 전에 웹사이트 데이터를 자동으로 다시 생성합니다.

```bash
npm run build
```

Cloudflare Pages 배포는 Functions(`functions/`)까지 포함되도록 아래 명령을 사용합니다. 배포 명령은 이미 생성된 `web/dist`를 올리므로, 먼저 `npm run build`를 실행합니다.

```bash
npm run deploy
```

8. 생성된 `issues/YYYY-MM-DD-running-newsletter.md`, `web/public/assets/issues/YYYY-MM-DD/`, `web/`을 열어 사람이 최종 검수합니다.
9. SMTP 환경변수와 `RUNEORRRI_SITE_BASE_URL`을 설정했다면 검수용 메일을 보냅니다.

```bash
python3 scripts/send_issue_email.py --recipients test --issue-id 2026-05-05-05
```

`npm run publish`는 발행 검증, 원고/이미지/웹 데이터 생성, 웹 빌드까지만 수행합니다. 구독자에게 메일을 보내지 않습니다.

```bash
npm run publish
```

구독자 전체 발송은 사용자가 "구독자에게 보내줘"라고 명시한 뒤에만 아래 명령으로 진행합니다. 이 명령은 작업 트리가 깨끗하고 현재 브랜치가 원격에 푸시된 상태일 때만 `send-newsletter.yml` 워크플로를 실행합니다.

```bash
npm run send:subscribers
```

메일 발송 전 `scripts/send_issue_email.py`는 생성된 웹 데이터를 읽고, 메일 상단 링크와 히어로 이미지를 `RUNEORRRI_SITE_BASE_URL/NN`(회차 번호)으로 연결합니다. 기본값은 검수용 `MAIL_TO` 발송이며, 구독자 발송은 D1의 `active` 구독자 목록을 사용합니다.

뉴스레터 원고는 이메일 본문 텍스트와 웹사이트 데이터의 원천으로 사용하고, `web/public/assets/issues/YYYY-MM-DD/` 이미지는 메일 인라인 이미지와 웹사이트 대표 이미지로 함께 사용합니다.

## 표준 자동화 파이프라인

아래 명령 하나가 발행 전 후보 검증, 원고 생성, 메일/웹 이미지 생성, 웹 데이터 생성을 순서대로 실행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id 2026-05-05-05
```

검수용 메일은 `.env` 설정 후 별도로 보냅니다.

```bash
python3 scripts/send_issue_email.py --recipients test --issue-id 2026-05-05-05
```

발행 작업에서는 `today`보다 명시적인 `issue-id`를 권장합니다. `today`와 `latest`는 보조 옵션입니다.

## 자료 수집 요청을 받았을 때

사용자가 "자료수집 해줘"라고 요청하면 바로 발행하지 않고 아래 순서로 진행합니다.

1. `docs/editorial-guidelines.md`를 기준으로 최근 48~72시간 러닝 소식 10개를 찾습니다.
2. 기존 발행호(`issues/`, `web/src/data/issues.json`, `data/candidates_archive.csv`의 selected rows)를 먼저 대조합니다.
   같은 대회, 같은 브랜드/제품군, 같은 엘리트 레이스, 같은 기사 URL, 같은 주제 후속 기사처럼 보이면 제외합니다.
3. 후보 10개를 `data/candidates_archive.csv`에 같은 `issue_id`로 추가합니다.
   이 단계에서는 기본값을 `selected=no`로 둡니다.
4. 아래 명령으로 10개 후보 풀을 검증합니다. 이 검증은 추천 전 단계이므로 10개 모두 `selected=no`일 때만 통과합니다.

```bash
python3 scripts/validate_candidate_pool.py 2026-05-05-05 --mode collect
```

5. 에디터 추천 5개를 정한 뒤, 추천 row 번호를 넣어 추천 조합도 검증합니다.

```bash
python3 scripts/validate_candidate_pool.py 2026-05-05-05 --mode collect --recommend 1,2,5,7,9
```

6. 검증을 통과한 뒤 사용자에게 후보 10개를 제목, 출처, 왜 중요한지 중심으로 보여주고, 그중 에디터 추천 5개를 함께 표시합니다.
   추천 5개는 국내 일반 러너에게 바로 쓸모 있는 순서, 마감 임박성, 카테고리 균형, 기존 발행호와의 차별성을 기준으로 고릅니다.
   추천은 아직 승인으로 보지 않으며, 사용자가 "추천대로"라고 하거나 다른 5개를 지정하기 전까지는 `selected=no`를 유지합니다.
7. 사용자가 승인한 5개만 `selected=yes`로 바꿉니다.
8. 아래 명령으로 발행 검증과 생성까지 진행합니다.

```bash
python3 scripts/run_newsletter_pipeline.py --issue-id 2026-05-05-05
```

9. 사용자가 "메일발송해줘"라고 하면 검수용 `MAIL_TO`로만 발송합니다.
   사용자가 "구독자에게 보내줘"라고 명시한 뒤에만 `npm run send:subscribers`로 GitHub Actions 워크플로를 실행합니다.
   워크플로는 검증과 생성, 웹 빌드, Cloudflare Pages 배포, 라이브 확인, D1의 `active` 구독자 발송을 한 번에 처리합니다.

## 발송 설정

GitHub Actions 워크플로 `.github/workflows/send-newsletter.yml`은 예약 실행하지 않습니다. 수동 실행(`workflow_dispatch`)에서 `confirm_subscriber_send`를 `true`로 지정한 경우에만 실행됩니다. 워크플로는 웹 배포와 라이브 확인을 먼저 끝내고, 마지막 단계에서 구독자에게 메일을 발송합니다.

검수용 메일은 수동으로 `--recipients test`를 사용합니다. 구독자 전체 발송은 `npm run send:subscribers` 또는 워크플로 수동 실행으로만 진행합니다.

Cloudflare Pages 배포 설정은 저장소 루트 기준으로 봅니다.

- 빌드 명령: `npm run build`
- 빌드 출력: `web/dist`
- Pages Functions 위치: `functions/`

검수용 이메일 발송은 `.env.example`을 참고해 `.env` 파일에 SMTP 설정과 `MAIL_TO`를 넣습니다. 구독자 전체 발송은 GitHub Actions 저장소 시크릿의 Cloudflare D1 설정과 SMTP 설정을 사용합니다.

## 발행 전 필수 체크

- 모든 소식에 원문 링크가 있는가?
- 대회, 접수, 제품명, 가격, 날짜를 공식 출처로 확인했는가?
- 해외 소식에 한국 러너에게 필요한 맥락을 붙였는가?
- 보도자료성 콘텐츠를 광고처럼 쓰지 않았는가?
- 저장 또는 공유를 유도할 만한 소식이 최소 1개 있는가?

## 발행 후 확인

- 최신 회차가 `/NN` 경로로 열리는지 확인합니다.
- 검수용 메일을 보냈다면 히어로·체크포인트 이미지가 모두 표시되고 상단 링크가 해당 회차로 연결되는지 확인합니다.
- 구독자 메일 하단에는 작은 수신거부 링크가 있어야 합니다.
