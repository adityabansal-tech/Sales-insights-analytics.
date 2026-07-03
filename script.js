async function loadData() {
  const res = await fetch('dashboard_data.json');
  const data = await res.json();
  return data;
}

function fmtCurrency(v) {
  return '$' + Number(v).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
}

function initKpis(kpi) {
  document.getElementById('k-revenue').textContent = fmtCurrency(kpi.total_revenue);
  document.getElementById('k-profit').textContent = fmtCurrency(kpi.total_profit);
  document.getElementById('k-orders').textContent = Number(kpi.total_orders).toLocaleString();
  document.getElementById('k-aov').textContent = fmtCurrency(kpi.avg_order_value);
  if (dataGlobal && dataGlobal.benchmark && dataGlobal.benchmark.speedup_pct !== undefined) {
    document.getElementById('k-speedup').textContent = dataGlobal.benchmark.speedup_pct + '%';
  } else {
    document.getElementById('k-speedup').textContent = 'N/A';
  }
}

function buildLineChart(ctx, labels, series, label) {
  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: series },
    options: {
      responsive: true,
      plugins: { legend: { display: true, labels: { color: '#cbd9ff' } } },
      scales: {
        x: { ticks: { color: '#9aa6b2' }, grid: { color: 'rgba(255,255,255,0.02)' } },
        y: { ticks: { color: '#9aa6b2' }, grid: { color: 'rgba(255,255,255,0.02)' } }
      }
    }
  });
}

function buildBarChart(ctx, labels, values, label) {
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{label, data: values, backgroundColor: '#1f6feb'}] },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#9aa6b2' } },
        y: { ticks: { color: '#9aa6b2' } }
      }
    }
  });
}

function populateTable(rows) {
  const tbody = document.getElementById('customers-body');
  tbody.innerHTML = '';
  for (const r of rows) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.customer_id}</td>
      <td>${r.customer_name}</td>
      <td>${r.segment}</td>
      <td>${r.last_order_date}</td>
      <td>${Number(r.frequency).toLocaleString()}</td>
      <td>${fmtCurrency(r.monetary_value)}</td>
    `;
    tbody.appendChild(tr);
  }
}

let dataGlobal = null;

async function boot() {
  const data = await loadData();
  dataGlobal = data;
  const kpi = data.kpi && data.kpi.length ? data.kpi[0] : {};
  initKpis(kpi);

  // monthly
  const months = data.monthly.map(m => `${m.year}-${String(m.month).padStart(2,'0')}`);
  const revenue = data.monthly.map(m => Number(m.total_revenue));
  const profit = data.monthly.map(m => Number(m.total_profit));
  buildLineChart(document.getElementById('chart-monthly').getContext('2d'), months, [
    { label: 'Revenue', data: revenue, borderColor: '#1f6feb', backgroundColor: 'rgba(31,111,235,0.08)', fill: true },
    { label: 'Profit', data: profit, borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.06)', fill: true }
  ]);

  // categories
  const catLabels = data.categories.map(c => c.category);
  const catValues = data.categories.map(c => Number(c.total_revenue));
  buildBarChart(document.getElementById('chart-categories').getContext('2d'), catLabels, catValues, 'Revenue');

  // top products
  const prodLabels = data.products.slice(0, 10).map(p => p.product_name);
  const prodValues = data.products.slice(0, 10).map(p => Number(p.total_revenue));
  buildBarChart(document.getElementById('chart-products').getContext('2d'), prodLabels, prodValues, 'Revenue');

  // regional
  const regLabels = data.regional.map(r => r.country);
  const regValues = data.regional.map(r => Number(r.total_revenue));
  buildBarChart(document.getElementById('chart-regional').getContext('2d'), regLabels, regValues, 'Revenue');

  // customers table
  populateTable(data.customers.slice(0, 100));

  // benchmark chart
  if (data.benchmark) {
    const withoutMs = data.benchmark.without_avg_ms || null;
    const withMs = data.benchmark.with_avg_ms || null;
    const labels = ['Without Indexes', 'With Indexes'];
    const vals = [withoutMs, withMs];
    buildBarChart(document.getElementById('chart-benchmark').getContext('2d'), labels, vals, 'ms');
  }
}

boot().catch(e => {
  console.error('Dashboard load error:', e);
  document.body.innerHTML += '<div style="color:red;padding:20px">Error loading dashboard: ' + e.message + '</div>';
});
