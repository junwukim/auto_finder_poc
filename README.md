# Shoe Deal Tracker (PoC)

정적 HTML로 시작하는 **신발 딜 트래커 PoC 템플릿**입니다.

- 4시간마다 크롤링(샘플 HTML 기준) → `docs/data/deals.json` 생성
- `docs/index.html`에서 딜 리스트 표시
- 나중에 AdSense 배너/도메인/DB로 확장 가능

> ⚠️ 실제 쇼핑몰을 크롤링할 때는 각 사이트의 ToS/robots.txt를 준수하고,
> 과도한 요청(짧은 주기/대량)을 피하세요.

---

## 폴더 구조

```
shoe-deal-tracker-poc/
  config/
    targets.json          # 크롤링 대상(브랜드/모델/URL/셀렉터/기준가/임계치)
  scripts/
    crawl_and_build.py    # 크롤링 실행 → history 업데이트 → deals.json 생성
    crawler.py            # 페이지에서 가격/사이즈 파싱 (requests+bs4)
    utils.py
  data/
    history.json          # (PoC) 가격 히스토리 누적 (repo에 커밋)
  docs/                   # GitHub Pages 배포 폴더
    index.html
    p.html
    about.html
    privacy.html
    terms.html
    contact.html
    data/
      deals.json          # 프론트가 읽는 결과물
    samples/              # PoC용 샘플 상품 페이지(웹에서 클릭해 볼 수 있음)
      store1.html
      store2.html
    assets/
      style.css
      app.js
  .github/workflows/
    crawl.yml             # 4시간마다 자동 실행(GitHub Actions)
```

---

## 1) 로컬에서 바로 실행하기

### 1-1. 크롤러 실행 (JSON 생성)
```bash
# repo 루트에서
pip install -r requirements.txt
python scripts/crawl_and_build.py
```

성공하면:
- `docs/data/deals.json` 가 생성/갱신됩니다.

### 1-2. 정적 웹 실행(로컬)
```bash
cd docs
python -m http.server 8000
```

브라우저에서:
- http://localhost:8000/index.html

---

## 2) GitHub에 올려서 Pages로 배포하기

### 2-1. GitHub 저장소 생성 후 push
```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

### 2-2. GitHub Pages 설정
- GitHub repo → **Settings** → **Pages**
- **Build and deployment**
  - Source: **Deploy from a branch**
  - Branch: `main`
  - Folder: `/docs`
- 저장하면 `https://<username>.github.io/<repo>/` 로 배포됩니다.

### 2-3. Actions가 push 할 수 있게 설정(필요할 수 있어요)
- Settings → Actions → General
- Workflow permissions: **Read and write permissions** 선택

### 2-4. 4시간 자동 갱신 확인
- Actions 탭에서 `Crawl and build deals` 워크플로우가 스케줄로 실행됩니다.
- `docs/data/deals.json` 가 업데이트되면 페이지도 자동 갱신됩니다.

> cron은 **UTC 기준**입니다. 한국시간(KST)은 UTC+9.
> 워크플로는 매 4시간마다 **UTC 기준 7분**에 실행되도록 설정돼 있어요(혼잡 시간 회피).

---

## 3) 실제 사이트로 확장하기 (targets.json 수정)

`config/targets.json`에 사이트별 URL과 CSS selector를 추가하세요.

예시:
```json
{
  "seller": "SomeStore",
  "url": "https://example.com/product/123",
  "selectors": {
    "price": ".price",
    "sizes": ".size-option"
  },
  "baseline_price": 200000,
  "discount_threshold": 0.15
}
```

- `price`: 가격이 들어있는 요소(텍스트)
- `sizes`: 사이즈 옵션 요소들(텍스트)
- `baseline_price`: “평소가/기준가”(처음엔 직접 넣는 게 제일 쉬움)
- `discount_threshold`: 할인 임계치(0.10 = 10%)

---

## 4) 광고(AdSense) 붙이기(나중에)

- `docs/index.html`, `docs/p.html`에 **[AD SLOT]** 주석이 있는 영역이 배너 자리입니다.
- 도메인을 연결한 뒤 AdSense 승인/광고 코드를 넣고,
- `ads.txt`는 `docs/ads.txt`로 두면(루트에 노출되게) 됩니다.

(ads.txt는 발급받은 pub-id로 생성해야 하므로, PoC 단계에선 굳이 넣지 않아도 됩니다.)
