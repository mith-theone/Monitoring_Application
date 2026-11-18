/* Dashboard metrics poll — authenticated endpoint only; no credentials in query. */
(function () {
  const REFRESH_MS = 5000;
  const select = document.getElementById("target-select");
  const refreshBtn = document.getElementById("refresh-btn");
  const errEl = document.getElementById("metrics-error");
  const statusEl = document.getElementById("metrics-status");
  const cpuBody = document.getElementById("cpu-body");
  const memBody = document.getElementById("mem-body");
  const netBody = document.getElementById("net-body");
  const portsBody = document.getElementById("ports-body");

  let timer = null;
  let cpuChart = null;
  let memChart = null;
  const cpuHistory = [];
  const memHistory = [];
  const labels = [];
  const MAX_POINTS = 12;

  function fmtBytes(n) {
    if (n == null) return "—";
    const u = ["B", "KB", "MB", "GB", "TB"];
    let v = Number(n);
    let i = 0;
    while (v >= 1024 && i < u.length - 1) {
      v /= 1024;
      i += 1;
    }
    return v.toFixed(i === 0 ? 0 : 1) + " " + u[i];
  }

  function ensureCharts() {
    if (typeof Chart === "undefined") return;
    if (!cpuChart) {
      cpuChart = new Chart(document.getElementById("cpu-chart"), {
        type: "line",
        data: {
          labels,
          datasets: [{ label: "CPU %", data: cpuHistory, borderColor: "#1f6feb", tension: 0.25 }],
        },
        options: {
          animation: false,
          scales: { y: { min: 0, max: 100 } },
          plugins: { legend: { display: false } },
        },
      });
    }
    if (!memChart) {
      memChart = new Chart(document.getElementById("mem-chart"), {
        type: "line",
        data: {
          labels,
          datasets: [{ label: "Mem %", data: memHistory, borderColor: "#1a7f4b", tension: 0.25 }],
        },
        options: {
          animation: false,
          scales: { y: { min: 0, max: 100 } },
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  function pushHistory(cpuPct, memPct) {
    const t = new Date().toLocaleTimeString();
    labels.push(t);
    cpuHistory.push(cpuPct);
    memHistory.push(memPct);
    if (labels.length > MAX_POINTS) {
      labels.shift();
      cpuHistory.shift();
      memHistory.shift();
    }
    if (cpuChart) {
      cpuChart.update();
      memChart.update();
    }
  }

  function showError(msg) {
    errEl.hidden = false;
    errEl.textContent = msg || "Host unreachable";
    cpuBody.className = "empty-state";
    cpuBody.textContent = "Unavailable";
    memBody.className = "empty-state";
    memBody.textContent = "Unavailable";
    netBody.className = "empty-state";
    netBody.textContent = "Unavailable";
    portsBody.className = "empty-state";
    portsBody.textContent = "Unavailable";
  }

  function render(data) {
    if (!data || data.ok === false) {
      showError((data && data.error) || "Host unreachable");
      statusEl.textContent = "Last update failed";
      return;
    }
    errEl.hidden = true;
    ensureCharts();
    const cpuPct = (data.cpu && data.cpu.percent) || 0;
    const memPct = (data.memory && data.memory.percent) || 0;
    pushHistory(cpuPct, memPct);

    cpuBody.className = "metric-body";
    cpuBody.textContent = cpuPct.toFixed(1) + "% used";

    const m = data.memory || {};
    memBody.className = "metric-body";
    memBody.innerHTML =
      memPct.toFixed(1) +
      "% · used " +
      fmtBytes(m.used) +
      " / " +
      fmtBytes(m.total) +
      "<br>free " +
      fmtBytes(m.free) +
      " · swap " +
      fmtBytes(m.swap_used) +
      " / " +
      fmtBytes(m.swap_total);

    const nets = data.network || [];
    if (!nets.length) {
      netBody.className = "empty-state";
      netBody.textContent = "No interfaces";
    } else {
      netBody.className = "metric-body";
      netBody.innerHTML = nets
        .slice(0, 8)
        .map(function (n) {
          return (
            "<div><strong>" +
            n.interface +
            "</strong> in " +
            fmtBytes(n.bytes_recv) +
            " · out " +
            fmtBytes(n.bytes_sent) +
            "</div>"
          );
        })
        .join("");
    }

    const ports = data.ports || [];
    if (!ports.length) {
      portsBody.className = "empty-state";
      portsBody.textContent = "No listening ports (or permission limited)";
    } else {
      portsBody.className = "metric-body";
      portsBody.innerHTML = ports
        .slice(0, 20)
        .map(function (p) {
          return (
            "<div>" +
            p.proto +
            "/" +
            p.port +
            (p.process ? " · " + p.process : "") +
            "</div>"
          );
        })
        .join("");
    }

    statusEl.textContent =
      "Updated " +
      new Date().toLocaleTimeString() +
      " · " +
      (data.display_name || data.target || "") +
      " (" +
      (data.source || "") +
      ")";
  }

  function loadMetrics() {
    const target = select ? select.value : "localhost";
    const url = "/api/metrics?target=" + encodeURIComponent(target);
    fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) {
        if (r.status === 401 || r.status === 302) {
          window.location.href = "/login";
          return null;
        }
        return r.json();
      })
      .then(function (data) {
        if (data) render(data);
      })
      .catch(function () {
        showError("Host unreachable");
        statusEl.textContent = "Request failed";
      });
  }

  function schedule() {
    if (timer) clearInterval(timer);
    timer = setInterval(loadMetrics, REFRESH_MS);
  }

  if (select) {
    select.addEventListener("change", function () {
      const url = new URL(window.location.href);
      url.searchParams.set("target", select.value);
      window.history.replaceState({}, "", url);
      loadMetrics();
    });
  }
  if (refreshBtn) refreshBtn.addEventListener("click", loadMetrics);

  loadMetrics();
  schedule();
})();
