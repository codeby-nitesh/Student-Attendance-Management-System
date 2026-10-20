// Main UI JavaScript Initialization
document.addEventListener('DOMContentLoaded', function () {
  // 1. Sidebar toggle for mobile responsive
  const navToggleBtn = document.getElementById('navToggleBtn');
  const sidebar = document.getElementById('sidebar');

  if (navToggleBtn && sidebar) {
    navToggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (event) {
      if (window.innerWidth < 992) {
        if (!sidebar.contains(event.target) && !navToggleBtn.contains(event.target)) {
          sidebar.classList.remove('show');
        }
      }
    });
  }

  // 2. Initialize Bootstrap tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 3. Auto-dismiss alerts after 5 seconds
  const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
  autoDismissAlerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
});
