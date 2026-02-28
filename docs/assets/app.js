/* PoC front-end logic (no framework) */

function qs(id) { return document.getElementById(id); }

function formatMoney(n, currency) {
  if (n === null || n === undefined) return "-";
  try {
    const num = Number(n);
    return new Intl.NumberFormat("ko-KR").format(num) + " " + (currency || "");
  } catch {
    return String(n) + " " + (currency || "");
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadDeals() {
  const bust = Date.now();
  const res = await fetch(`data/deals.json?t=${bust}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load deals.json: ${res.status}`);
  return res.json();
}

function renderIndex(data) {
  const deals = (data && data.deals) ? data.deals : [];
  const statusText = qs("statusText");
  const statusTime = qs("statusTime");
  const tbody = qs("dealsBody");
  const empty = qs("emptyState");
  const filterBrand = qs("filterBrand");
  const filterMinDiscount = qs("filterMinDiscount");

  if (!tbody || !statusText) return; // not on index page

  statusText.textContent = `딜 ${deals.length}개`;
  statusTime.textContent = data.generated_at ? `업데이트: ${data.generated_at}` : "";

  // Populate brand filter
  const brands = Array.from(new Set(deals.map(d => d.brand).filter(Boolean))).sort();
  filterBrand.innerHTML = `<option value="">전체</option>` + brands.map(b => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join("");

  function applyFilters() {
    const brand = filterBrand.value;
    const minD = Number(filterMinDiscount.value || 0);

    const filtered = deals.filter(d => {
      const okBrand = !brand || d.brand === brand;
      const okDisc = (Number(d.discount_percent) || 0) >= minD;
      return okBrand && okDisc;
    });

    tbody.innerHTML = filtered.map(d => {
      const sizes = (d.sizes_available || []).slice(0, 10).map(s => `<span class="badge">${escapeHtml(s)}</span>`).join("")
        + ((d.sizes_available || []).length > 10 ? `<span class="badge">+${(d.sizes_available || []).length - 10}</span>` : "");
      const price = formatMoney(d.price, d.currency);
      const disc = `${d.discount_percent}%`;
      const link = `p.html?id=${encodeURIComponent(d.id)}`;
      const sellerLink = `<a href="${escapeHtml(d.url)}" target="_blank" rel="noreferrer">${escapeHtml(d.seller)}</a>`;

      return `
        <tr>
          <td>${escapeHtml(d.brand || "-")}</td>
          <td><a href="${link}">${escapeHtml(d.model || "-")}</a></td>
          <td>${sellerLink}</td>
          <td class="num">${escapeHtml(price)}</td>
          <td class="num">${escapeHtml(disc)}</td>
          <td>${sizes || "-"}</td>
          <td>${escapeHtml(d.last_seen_at || "-")}</td>
        </tr>
      `;
    }).join("");

    empty.hidden = filtered.length !== 0;
  }

  filterBrand.addEventListener("change", applyFilters);
  filterMinDiscount.addEventListener("change", applyFilters);
  qs("btnRefresh").addEventListener("click", () => window.location.reload());

  applyFilters();
}

function renderDetail(data) {
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");
  const title = qs("title");
  const card = qs("detailCard");
  if (!title || !card) return; // not on detail page
  if (!id) {
    title.textContent = "딜 ID가 없습니다.";
    card.innerHTML = "<p>index.html에서 항목을 클릭해 들어오세요.</p>";
    return;
  }

  const deal = (data.deals || []).find(d => d.id === id);
  if (!deal) {
    title.textContent = "해당 딜을 찾을 수 없습니다.";
    card.innerHTML = "<p>딜이 만료되었거나 데이터가 갱신되어 사라졌을 수 있어요.</p>";
    return;
  }

  title.textContent = `${deal.brand} / ${deal.model}`;

  const sizes = (deal.sizes_available || []).map(s => `<span class="badge">${escapeHtml(s)}</span>`).join("") || "-";

  card.innerHTML = `
    <p class="muted">업데이트: ${escapeHtml(deal.last_seen_at || "-")}</p>
    <p>
      <strong>판매처:</strong> <a href="${escapeHtml(deal.url)}" target="_blank" rel="noreferrer">${escapeHtml(deal.seller)}</a>
    </p>
    <p><strong>현재가:</strong> ${escapeHtml(formatMoney(deal.price, deal.currency))}</p>
    <p><strong>기준가:</strong> ${escapeHtml(formatMoney(deal.baseline_price, deal.currency))}</p>
    <p><strong>할인율:</strong> ${escapeHtml(String(deal.discount_percent))}% (${escapeHtml(deal.rule || "")})</p>
    <p><strong>가능 사이즈:</strong> ${sizes}</p>
    <hr />
    <p class="muted">
      PoC 단계에서는 샘플 HTML을 읽어옵니다. 실제 적용 시 <code>config/targets.json</code>에 사이트 URL과 파싱 셀렉터를 추가하세요.
    </p>
  `;
}

(async function boot() {
  try {
    const data = await loadDeals();
    renderIndex(data);
    renderDetail(data);
  } catch (e) {
    const statusText = qs("statusText");
    if (statusText) statusText.textContent = "데이터 로드 실패";
    const card = qs("detailCard");
    if (card) card.innerHTML = `<p>데이터 로드 실패: ${escapeHtml(e.message || String(e))}</p>`;
    console.error(e);
  }
})();
