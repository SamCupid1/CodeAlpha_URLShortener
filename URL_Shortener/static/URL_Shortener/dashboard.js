(() => {
  const canvas = document.getElementById("click-chart");
  if (!canvas || !window.Chart) return;

  const labels = JSON.parse(document.getElementById("chart-labels").textContent);
  const values = JSON.parse(document.getElementById("chart-values").textContent);
  const formattedLabels = labels.map((day) =>
    new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(
      new Date(`${day}T12:00:00`),
    ),
  );

  new window.Chart(canvas, {
    type: "line",
    data: {
      labels: formattedLabels,
      datasets: [
        {
          label: "Clicks",
          data: values,
          borderColor: "#2459d3",
          backgroundColor: "rgba(36, 89, 211, 0.10)",
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#ffffff",
          pointBorderColor: "#2459d3",
          pointBorderWidth: 2,
          fill: true,
          tension: 0.35,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { displayColors: false },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#718096", maxRotation: 0, autoSkip: true, maxTicksLimit: 7 },
          border: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { color: "#718096", precision: 0 },
          grid: { color: "#edf1f7" },
          border: { display: false },
        },
      },
    },
  });
})();
