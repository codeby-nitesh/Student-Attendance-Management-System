// Attendance Marking Helper
document.addEventListener('DOMContentLoaded', function () {
  const markAllPresentBtn = document.getElementById('markAllPresentBtn');
  const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');

  function updateLiveCounters() {
    const radios = document.querySelectorAll('input[type="radio"]:checked');
    let present = 0, absent = 0, late = 0, leave = 0;

    radios.forEach(function (r) {
      if (r.value === 'Present') present++;
      else if (r.value === 'Absent') absent++;
      else if (r.value === 'Late') late++;
      else if (r.value === 'Leave') leave++;
    });

    const pEl = document.getElementById('counterPresent');
    const aEl = document.getElementById('counterAbsent');
    const lEl = document.getElementById('counterLate');
    const lvEl = document.getElementById('counterLeave');

    if (pEl) pEl.textContent = present;
    if (aEl) aEl.textContent = absent;
    if (lEl) lEl.textContent = late;
    if (lvEl) lvEl.textContent = leave;
  }

  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', function () {
      const presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
      presentRadios.forEach(function (radio) {
        radio.checked = true;
      });
      updateLiveCounters();
    });
  }

  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', function () {
      const absentRadios = document.querySelectorAll('input[type="radio"][value="Absent"]');
      absentRadios.forEach(function (radio) {
        radio.checked = true;
      });
      updateLiveCounters();
    });
  }

  // Listen to individual radio changes
  const allRadios = document.querySelectorAll('.attendance-btn-group input[type="radio"]');
  allRadios.forEach(function (radio) {
    radio.addEventListener('change', updateLiveCounters);
  });

  // Initial count calculation
  updateLiveCounters();
});
