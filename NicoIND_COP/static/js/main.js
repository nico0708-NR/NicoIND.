/* ════════════════════════════════════════════════════════════
   NicoIND — main.js
   Author: Nicolás Rodríguez
   ════════════════════════════════════════════════════════════ */
'use strict';

// ─── Flash Messages ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach((el, i) => {
    el.addEventListener('click', () => dismissFlash(el));
    setTimeout(() => dismissFlash(el), 5000 + i * 400);
  });
});

function dismissFlash(el) {
  el.style.transition = 'opacity .3s, transform .3s';
  el.style.opacity = '0';
  el.style.transform = 'translateX(110px)';
  setTimeout(() => el.remove(), 350);
}

// ─── Sidebar Toggle ───────────────────────────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('open');
}

document.addEventListener('click', (e) => {
  const sb = document.getElementById('sidebar');
  if (!sb) return;
  if (sb.classList.contains('open') &&
      !sb.contains(e.target) &&
      !e.target.closest('.menu-btn')) {
    sb.classList.remove('open');
  }
});

// ─── Chart Defaults ───────────────────────────────────────────
const CHART_COLORS = {
  purple:  '#7c3aed', purpleL: '#a78bfa', purpleA: 'rgba(124,58,237,.15)',
  blue:    '#0ea5e9', blueL:   '#7dd3fc', blueA:   'rgba(14,165,233,.15)',
  green:   '#10b981', greenL:  '#6ee7b7', greenA:  'rgba(16,185,129,.15)',
  amber:   '#f59e0b', amberL:  '#fcd34d', amberA:  'rgba(245,158,11,.15)',
  red:     '#ef4444', redL:    '#fca5a5',
  text2:   '#8b949e', border:  '#30363d', bg3: '#1c2128',
};

function chartDefaults() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#161b22',
        borderColor: '#30363d', borderWidth: 1,
        titleColor: '#e6edf3', bodyColor: '#8b949e',
        padding: 10,
      }
    }
  };
}

function axesDefaults() {
  return {
    y: { beginAtZero: true,
         grid: { color: 'rgba(48,54,61,.6)' },
         ticks: { color: '#484f58', font: { size: 11 } },
         border: { display: false }
    },
    x: { grid: { display: false },
         ticks: { color: '#484f58', font: { size: 11 } },
         border: { display: false }
    }
  };
}

// ─── Dashboard Charts ─────────────────────────────────────────
function initDashboardCharts(salesJSON, catJSON) {
  const sales = JSON.parse(salesJSON || '[]');
  const cats  = JSON.parse(catJSON  || '[]');

  const lc = document.getElementById('salesChart');
  if (lc) {
    new Chart(lc, {
      type: 'line',
      data: {
        labels: sales.map(d => d.date),
        datasets: [
          { label: 'Ventas', data: sales.map(d => d.sales),
            borderColor: CHART_COLORS.purple, backgroundColor: CHART_COLORS.purpleA,
            borderWidth: 2, fill: true, tension: .4,
            pointRadius: 3, pointBackgroundColor: CHART_COLORS.purple },
          { label: 'Gastos', data: sales.map(d => d.expenses),
            borderColor: CHART_COLORS.red, backgroundColor: 'rgba(239,68,68,.08)',
            borderWidth: 2, fill: true, tension: .4,
            pointRadius: 3, pointBackgroundColor: CHART_COLORS.red },
        ]
      },
      options: { ...chartDefaults(),
        plugins: { ...chartDefaults().plugins,
          legend: { display: true, position: 'top',
                    labels: { color: '#8b949e', boxWidth: 10, padding: 16, font: { size: 12 } } }
        },
        scales: axesDefaults()
      }
    });
  }

  const dc = document.getElementById('catChart');
  if (dc && cats.length) {
    const colors = [CHART_COLORS.purple, CHART_COLORS.blue, CHART_COLORS.green,
                    CHART_COLORS.amber, CHART_COLORS.red, '#8b5cf6', '#06b6d4'];
    new Chart(dc, {
      type: 'doughnut',
      data: {
        labels: cats.map(c => c.label),
        datasets: [{ data: cats.map(c => c.value),
                     backgroundColor: colors.slice(0, cats.length),
                     borderWidth: 0, hoverOffset: 4 }]
      },
      options: { ...chartDefaults(), cutout: '65%',
        plugins: { ...chartDefaults().plugins,
          legend: { display: true, position: 'bottom',
                    labels: { color: '#8b949e', boxWidth: 10, padding: 14, font: { size: 11 } } }
        }
      }
    });
  }
}

// ─── Finance Chart ────────────────────────────────────────────
function initFinanceChart(dataJSON) {
  const data = JSON.parse(dataJSON || '[]');
  const ctx  = document.getElementById('financeChart');
  if (!ctx || !data.length) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.date),
      datasets: [
        { label: 'Ingresos', data: data.map(d => d.income),
          backgroundColor: CHART_COLORS.greenA, borderColor: CHART_COLORS.green,
          borderWidth: 1.5, borderRadius: 4 },
        { label: 'Gastos', data: data.map(d => d.expense),
          backgroundColor: 'rgba(239,68,68,.12)', borderColor: CHART_COLORS.red,
          borderWidth: 1.5, borderRadius: 4 },
      ]
    },
    options: { ...chartDefaults(),
      plugins: { ...chartDefaults().plugins,
        legend: { display: true, position: 'top',
                  labels: { color: '#8b949e', boxWidth: 10, padding: 16, font: { size: 12 } } }
      },
      scales: axesDefaults()
    }
  });
}

// ─── BI Monthly Chart ─────────────────────────────────────────
function initBIChart(dataJSON) {
  const data = JSON.parse(dataJSON || '[]');
  const ctx  = document.getElementById('biChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.month),
      datasets: [
        { label: 'Ventas', data: data.map(d => d.sales),
          borderColor: CHART_COLORS.purple, backgroundColor: CHART_COLORS.purpleA,
          borderWidth: 2.5, fill: true, tension: .4, pointRadius: 4 },
        { label: 'Gastos', data: data.map(d => d.expenses),
          borderColor: CHART_COLORS.amber, backgroundColor: CHART_COLORS.amberA,
          borderWidth: 2, fill: true, tension: .4, pointRadius: 3 },
      ]
    },
    options: { ...chartDefaults(),
      plugins: { ...chartDefaults().plugins,
        legend: { display: true, position: 'top',
                  labels: { color: '#8b949e', boxWidth: 10, padding: 16, font: { size: 12 } } }
      },
      scales: axesDefaults()
    }
  });
}

// ─── OEE Chart ────────────────────────────────────────────────
function initOEEChart(dataJSON, machines) {
  const data = JSON.parse(dataJSON || '[]');
  const ctx  = document.getElementById('oeeChart');
  if (!ctx || !data.length) return;
  const mList  = JSON.parse(machines || '[]');
  const colors = [CHART_COLORS.purple, CHART_COLORS.blue, CHART_COLORS.green];
  const datasets = mList.map((m, i) => ({
    label: m,
    data: data.map(d => d[m] || null),
    borderColor: colors[i % colors.length],
    backgroundColor: 'transparent',
    borderWidth: 2, tension: .4, pointRadius: 3
  }));
  new Chart(ctx, {
    type: 'line',
    data: { labels: data.map(d => d.date), datasets },
    options: { ...chartDefaults(),
      plugins: { ...chartDefaults().plugins,
        legend: { display: true, position: 'top',
                  labels: { color: '#8b949e', boxWidth: 10, padding: 14, font: { size: 11 } } },
        annotation: { annotations: [{
          type: 'line', mode: 'horizontal', scaleID: 'y', value: 85,
          borderColor: CHART_COLORS.green, borderWidth: 1.5, borderDash: [5,3],
          label: { enabled: true, content: 'World Class 85%', font: { size: 10 } }
        }]}
      },
      scales: axesDefaults()
    }
  });
}

// ─── AI Sales Chart ───────────────────────────────────────────
function initAISalesChart(histLabels, histVals, futureLabels, futureVals) {
  const ctx = document.getElementById('aiSalesChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: [...histLabels, ...futureLabels],
      datasets: [
        { label: 'Histórico', data: [...histVals, ...Array(futureLabels.length).fill(null)],
          borderColor: CHART_COLORS.blue, backgroundColor: CHART_COLORS.blueA,
          borderWidth: 2.5, fill: true, tension: .4, pointRadius: 3 },
        { label: 'Predicción 30d', data: [...Array(histLabels.length).fill(null), ...futureVals],
          borderColor: CHART_COLORS.purple, backgroundColor: CHART_COLORS.purpleA,
          borderWidth: 2, fill: true, tension: .4, borderDash: [6,3], pointRadius: 2 }
      ]
    },
    options: { ...chartDefaults(),
      plugins: { ...chartDefaults().plugins,
        legend: { display: true, position: 'top',
                  labels: { color: '#8b949e', boxWidth: 10, padding: 14, font: { size: 12 } } }
      },
      scales: axesDefaults()
    }
  });
}

// ─── Confirm Delete ───────────────────────────────────────────
function confirmDelete(form, name) {
  if (confirm(`¿Eliminar "${name}"? Esta acción no se puede deshacer.`)) {
    form.submit();
  }
}

// ─── Update Task Status (Kanban) ──────────────────────────────
function updateTask(taskId, status) {
  fetch(`/projects/task/update/${taskId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `status=${status}`
  })
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      const prog = document.getElementById('projProgress');
      if (prog) prog.style.width = data.progress + '%';
      const progVal = document.getElementById('projProgressVal');
      if (progVal) progVal.textContent = data.progress + '%';
    }
  })
  .catch(() => location.reload());
}

// ─── Stock Movement Modal ─────────────────────────────────────
function showMovementModal(productId, productName) {
  document.getElementById('mvProductId').value   = productId;
  document.getElementById('mvProductName').textContent = productName;
  document.getElementById('movementModal').style.display = 'flex';
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.style.display = 'none';
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
});

// ─── Copy to Clipboard ────────────────────────────────────────
function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check" style="color:var(--green)"></i>';
    setTimeout(() => btn.innerHTML = orig, 2000);
  });
}

// ─── Toggle Password Visibility ──────────────────────────────
function togglePwd(inputId, btn) {
  const inp = document.getElementById(inputId);
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.innerHTML = inp.type === 'password'
    ? '<i class="fas fa-eye"></i>'
    : '<i class="fas fa-eye-slash"></i>';
}

// ─── Show/Hide Auth Tab ───────────────────────────────────────
function showAuthTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('loginForm').style.display = isLogin ? 'block' : 'none';
  document.getElementById('regForm').style.display   = isLogin ? 'none'  : 'block';
  document.getElementById('loginTab').className = 'auth-tab' + (isLogin ? ' active' : '');
  document.getElementById('regTab').className   = 'auth-tab' + (isLogin ? '' : ' active');
}

// ─── Number Formatting ───────────────────────────────────────
function fmtNum(n) {
  return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
}
