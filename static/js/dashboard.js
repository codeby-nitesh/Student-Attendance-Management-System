// Dashboard Charts & Interactive Controls
document.addEventListener('DOMContentLoaded', function () {
  // Check if chart elements exist on this page
  const trendCtx = document.getElementById('attendanceTrendChart');
  const classCtx = document.getElementById('classWiseChart');
  const statusCtx = document.getElementById('todayStatusDoughnut');

  // Parse server injected data from window variables
  if (trendCtx && window.dashboardTrendData) {
    new Chart(trendCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: window.dashboardTrendData.dates,
        datasets: [
          {
            label: 'Present',
            data: window.dashboardTrendData.present,
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: '#059669',
            pointRadius: 4
          },
          {
            label: 'Absent',
            data: window.dashboardTrendData.absent,
            borderColor: '#dc2626',
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: '#dc2626',
            pointRadius: 4
          },
          {
            label: 'Late',
            data: window.dashboardTrendData.late,
            borderColor: '#d97706',
            backgroundColor: 'rgba(217, 119, 6, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: '#d97706',
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            padding: 10,
            titleFont: { size: 13, weight: 'bold' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#f1f5f9' },
            ticks: { precision: 0 }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  if (classCtx && window.dashboardClassData) {
    const classLabels = window.dashboardClassData.map(c => c.label);
    const classPcts = window.dashboardClassData.map(c => c.percentage);

    new Chart(classCtx.getContext('2d'), {
      type: 'bar',
      data: {
        labels: classLabels,
        datasets: [{
          label: 'Attendance %',
          data: classPcts,
          backgroundColor: '#2563eb',
          borderRadius: 6,
          maxBarThickness: 32
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: { color: '#f1f5f9' },
            ticks: {
              callback: function (val) { return val + '%'; }
            }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  if (statusCtx && window.dashboardStatusData) {
    const s = window.dashboardStatusData;
    const total = s.present + s.absent + s.late + s.leave;

    new Chart(statusCtx.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Absent', 'Late', 'Leave'],
        datasets: [{
          data: total === 0 ? [1, 0, 0, 0] : [s.present, s.absent, s.late, s.leave],
          backgroundColor: total === 0 ? ['#e2e8f0'] : ['#059669', '#dc2626', '#d97706', '#0284c7'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, font: { size: 11 } }
          }
        }
      }
    });
  }

  // Date selector form auto-submit
  const dateInput = document.getElementById('dashboardDateSelector');
  if (dateInput) {
    dateInput.addEventListener('change', function () {
      document.getElementById('dashboardDateForm').submit();
    });
  }
});
