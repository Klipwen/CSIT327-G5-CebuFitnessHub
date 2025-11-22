(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    const scheduleGrid = document.getElementById('scheduleGrid');

    const scheduleState = {
      classes: [],
    };

    const REFRESH_INTERVAL_MS = 15000;
    let refreshTimer = null;

    const scheduleStartMinutes = scheduleGrid ? parseInt(scheduleGrid.dataset.startMinutes, 10) : 450;
    const scheduleInterval = scheduleGrid ? parseInt(scheduleGrid.dataset.interval, 10) : 30;
    const rowOffset = scheduleGrid ? parseInt(scheduleGrid.dataset.rowOffset, 10) : 2;

    function timeToMinutes(value) {
      if (!value) return null;
      const [h, m] = value.split(':').map(Number);
      if (Number.isNaN(h) || Number.isNaN(m)) return null;
      return h * 60 + m;
    }

    function renderSchedule() {
      if (!scheduleGrid) return;
      scheduleGrid.querySelectorAll('.class-block').forEach(block => block.remove());

      const totalRows = 24;

      scheduleState.classes.forEach(entry => {
        const startMinutes = timeToMinutes(entry.start_time);
        const endMinutes = timeToMinutes(entry.end_time);
        if (startMinutes == null || endMinutes == null) return;

        let startRow = rowOffset + Math.floor((startMinutes - scheduleStartMinutes) / scheduleInterval);
        let endRow = startRow + (endMinutes - startMinutes) / scheduleInterval;

        if (endRow > totalRows) {
          endRow = totalRows;
        }

        const columnStart = entry.day_of_week + 1;
        if (startRow < rowOffset || columnStart < 2 || startRow >= endRow) return;

        const block = document.createElement('div');
        block.className = 'class-block';
        block.style.gridColumn = columnStart;
        block.style.gridRow = `${startRow} / ${endRow}`;
        const roomLine = entry.location && entry.location.trim() ? `<div class="class-room">Room: ${entry.location}</div>` : '';
        block.innerHTML = `
          <div class="class-name">${entry.class_name}</div>
          <div class="class-coach">Coach: ${entry.instructor_name}</div>
          ${roomLine}
        `;
        scheduleGrid.appendChild(block);
      });
    }

    function handleResponse(response) {
      if (response.ok) {
        return response.json();
      }
      return response.json().then(data => {
        const error = data && data.error ? data.error : 'Something went wrong.';
        return Promise.reject(error);
      });
    }

    function fetchSchedule() {
      const url = `/api/member-schedule/?t=${Date.now()}`;
      fetch(url, { cache: 'no-store' })
        .then(handleResponse)
        .then(data => {
          scheduleState.classes = data.classes || [];
          renderSchedule();
        })
        .catch(err => {
          console.error('Failed to load schedule:', err);
        });
    }

    function startAutoRefresh() {
      stopAutoRefresh();
      refreshTimer = setInterval(fetchSchedule, REFRESH_INTERVAL_MS);
    }

    function stopAutoRefresh() {
      if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
      }
    }

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        fetchSchedule();
        startAutoRefresh();
      } else {
        stopAutoRefresh();
      }
    });

    window.addEventListener('focus', () => {
      fetchSchedule();
    });

    fetchSchedule();
    startAutoRefresh();
  });
})();