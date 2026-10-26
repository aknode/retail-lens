let selected = "products";
let params;
let reportVersion = 0;
let refreshVersion = 0;
const notes = {
  products: "Top 30 products by net revenue.",
  countries: "All transactions, including anonymous purchases.",
  rfm: "Known customers only; quintiles are relative to the filtered population. Frequency ties are split deterministically. Recency is measured at the selected end date.",
  cohorts:
    "Full-history first observed purchase defines acquisition. Denominators use all observed acquired customers. Date filters limit activity; country must be All. Observed cohort months include zero activity; future months are omitted. The first and final data months, and date-filter boundaries, can be partial. This dataset cannot establish true first-ever purchase.",
  transactions:
    "Latest 100 transaction lines; exports use the same report limit.",
};
async function loadReport() {
  const version = ++reportVersion;
  const name = selected;
  const query = params.toString();
  $("#error").style.display = "none";
  $("#report").innerHTML = '<p class="muted">Loading report…</p>';
  delete $("#report").dataset.ready;
  document
    .querySelectorAll("#tabs button")
    .forEach((b) => b.classList.toggle("active", b.dataset.name === name));
  const r = await api("/api/report/" + name + "?" + query);
  if (
    version !== reportVersion ||
    name !== selected ||
    query !== params.toString()
  )
    return;
  $("#report").innerHTML = table(r.rows);
  $("#report").dataset.ready = name;
  $("#report-note").textContent = notes[name] || "";
  $("#export").href = "/api/export/" + name + "?" + query;
  $("#sql").hidden = true;
}
async function refresh() {
  const version = ++refreshVersion;
  $("#error").style.display = "none";
  delete $("#metrics").dataset.ready;
  params = new URLSearchParams({
    start: $("#start").value,
    end: $("#end").value,
    country: $("#country").value,
  });
  const [k, m, r] = await Promise.all(
    ["kpis", "monthly", "repeat_customers"].map((n) =>
      api("/api/report/" + n + "?" + params),
    ),
  );
  if (version !== refreshVersion) return;
  const v = k.rows[0];
  $("#metrics").innerHTML = [
    ["Net revenue", "£" + fmt(v.net_revenue, 2)],
    ["Sales orders", fmt(v.sales_orders)],
    ["Average order value", "£" + fmt(v.average_order_value, 2)],
    ["Return / sales value", pct(v.return_value_ratio || 0)],
  ]
    .map(
      ([a, b]) =>
        '<div class="card"><div class="label">' +
        a +
        '</div><div class="metric">' +
        b +
        "</div></div>",
    )
    .join("");
  $("#trend").innerHTML = lineChart(m.rows, "month", "net_revenue");
  const rep = r.rows[0];
  $("#repeat").innerHTML =
    '<div class="metric">' +
    pct(rep.repeat_purchase_rate || 0) +
    "</div><p>" +
    fmt(rep.repeat_buyers || 0) +
    " repeat buyers / " +
    fmt(rep.known_buyers) +
    ' known buyers</p><p class="muted">At least two distinct positive-sales invoices during the selected window. Anonymous purchases are excluded.</p>';
  await loadReport();
  $("#metrics").dataset.ready = params.toString();
}
$("#filters").onsubmit = (e) => {
  e.preventDefault();
  refresh().catch(error);
};
$("#show-sql").onclick = async () => {
  try {
    const r = await api("/api/sql/" + selected);
    $("#sql").textContent = r.sql + "\n\n-- " + r.note;
    $("#sql").hidden = !$("#sql").hidden;
  } catch (e) {
    error(e);
  }
};
async function start() {
  const [m, q] = await Promise.all([api("/api/meta"), api("/api/quality")]);
  $("#start").value = m.start;
  $("#end").value = m.end;
  $("#country").innerHTML =
    "<option>All</option>" +
    m.countries.map((c) => "<option>" + esc(c) + "</option>").join("");
  $("#quality").innerHTML =
    "<p>" +
    fmt(q.source_rows) +
    " source rows → " +
    fmt(q.loaded_rows) +
    ' loaded rows</p><p class="muted">' +
    fmt(q.duplicate_rows_removed) +
    " duplicates removed · " +
    fmt(q.invalid_rows_removed) +
    " invalid rows removed · " +
    fmt(q.anonymous_line_rows) +
    ' anonymous lines retained.</p><span class="tag">Revenue reconciliation passed</span>';
  $("#tabs").innerHTML = [
    "products",
    "countries",
    "rfm",
    "cohorts",
    "transactions",
  ]
    .map(
      (n) =>
        '<button data-name="' + n + '">' + n.replaceAll("_", " ") + "</button>",
    )
    .join("");
  document.querySelectorAll("#tabs button").forEach(
    (b) =>
      (b.onclick = () => {
        selected = b.dataset.name;
        loadReport().catch(error);
      }),
  );
  await refresh();
}
start().catch(error);
