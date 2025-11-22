(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    const scheduleGrid = document.getElementById('scheduleGrid');
    const editScheduleBtn = document.getElementById('editScheduleBtn');
    const modals = {
      options: document.getElementById('modalEditOptions'),
      add: document.getElementById('modalAddClass'),
      delete: document.getElementById('modalDeleteClass'),
      logout: document.getElementById('modalLogout'),
    };
    const openAddClassBtn = document.getElementById('openAddClass');
    const openDeleteClassBtn = document.getElementById('openDeleteClass');
    const addClassForm = document.getElementById('addClassForm');
    const deleteClassForm = document.getElementById('deleteClassForm');
    const deleteClassList = document.getElementById('deleteClassList');
    const addClassError = document.getElementById('addClassError');
    const deleteClassError = document.getElementById('deleteClassError');
    const deleteClassSubmit = document.getElementById('confirmDeleteClass');
    const alertBanner = document.getElementById('scheduleAlert');
    const logoutButton = document.getElementById('logoutBtn');
    const logoutConfirmBtn = document.getElementById('btnConfirmLogout');

    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.innerHTML = '<div class="loader-card"><div class="loader-spinner"></div><div class="loader-text">Loading…</div></div>';
    document.body.appendChild(loader);
    const showLoader = () => loader.classList.add('is-active');
    const hideLoader = () => loader.classList.remove('is-active');

    const scheduleState = {
      classes: [],
    };

    const scheduleStartMinutes = scheduleGrid ? parseInt(scheduleGrid.dataset.startMinutes, 10) : 450;
    const scheduleInterval = scheduleGrid ? parseInt(scheduleGrid.dataset.interval, 10) : 30;
    const rowOffset = scheduleGrid ? parseInt(scheduleGrid.dataset.rowOffset, 10) : 2;

    let activeModal = null;
    let lastFocusedElement = null;

    function trapFocus(e) {
      if (!activeModal || e.key !== 'Tab') return;
      const focusable = activeModal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    function openModal(modal, trigger) {
      if (!modal) return;
      lastFocusedElement = trigger || document.activeElement;
      modal.classList.add('show');
      modal.setAttribute('aria-hidden', 'false');
      activeModal = modal;
      const focusable = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length) {
        focusable[0].focus();
      }
      modal.addEventListener('keydown', trapFocus);
    }

    function closeModal(modal) {
      if (!modal) return;
      modal.classList.remove('show');
      modal.setAttribute('aria-hidden', 'true');
      modal.removeEventListener('keydown', trapFocus);
      if (activeModal === modal) {
        activeModal = null;
      }
      if (lastFocusedElement) {
        lastFocusedElement.focus();
        lastFocusedElement = null;
      }

      const form = modal.querySelector('form');
      if (form) {
        form.reset();
      }
      const errorEls = modal.querySelectorAll('.form-error');
      errorEls.forEach(el => (el.textContent = ''));
      if (modal.id === 'modalDeleteClass' && deleteClassSubmit) {
        deleteClassSubmit.disabled = true;
      }
    }

    function showAlert(type, message) {
      if (!alertBanner) return;
      alertBanner.textContent = message;
      alertBanner.classList.remove('is-success', 'is-error', 'is-visible');
      if (message) {
        alertBanner.classList.add('is-visible');
        if (type === 'success') {
          alertBanner.classList.add('is-success');
        } else {
          alertBanner.classList.add('is-error');
        }
      }
      if (message && type === 'success') {
        setTimeout(() => {
          alertBanner.classList.remove('is-visible', 'is-success', 'is-error');
        }, 4000);
      }
    }

    function timeToMinutes(value) {
      if (!value) return null;
      const [h, m] = value.split(':').map(Number);
      if (Number.isNaN(h) || Number.isNaN(m)) return null;
      return h * 60 + m;
    }

    function renderSchedule() {
      if (!scheduleGrid) return;
      scheduleGrid.querySelectorAll('.class-block').forEach(block => block.remove());

      // Total rows: 1 header + 23 time slots (7:30 AM to 7:00 PM = 11.5 hours = 23 intervals)
      const totalRows = 24; // Row 1 = header, Rows 2-24 = time slots

      scheduleState.classes.forEach(entry => {
        const startMinutes = timeToMinutes(entry.start_time);
        const endMinutes = timeToMinutes(entry.end_time);
        if (startMinutes == null || endMinutes == null) return;
        
        // Calculate start row: (start_time_in_minutes - 450) // 30 + 2
        // 450 = 7:30 AM in minutes, +2 because Row 1 = header, Row 2 = first time slot
        let startRow = rowOffset + Math.floor((startMinutes - scheduleStartMinutes) / scheduleInterval);
        
        // Calculate end row: (end_time_in_minutes - 450) // 30 + 2
        let endRow = startRow + (endMinutes - startMinutes) / scheduleInterval;

        
        // Cap endRow to prevent creating extra rows
        if (endRow > totalRows) {
          endRow = totalRows;
        }
        
        const columnStart = entry.day_of_week + 1; // column 1 is time labels
        if (startRow < rowOffset || columnStart < 2 || startRow >= endRow) return;

        const block = document.createElement('div');
        block.className = 'class-block';
        block.style.gridColumn = columnStart;
        block.style.gridRow = `${startRow} / ${endRow}`;
        block.innerHTML = `
          <div class="class-name">${entry.class_name}</div>
          <div class="class-coach">Coach: ${entry.instructor_name}</div>
        `;
        scheduleGrid.appendChild(block);
      });
    }

    function populateDeleteList() {
      if (!deleteClassList) return;
      deleteClassList.innerHTML = '';
      if (!scheduleState.classes.length) {
        deleteClassList.innerHTML = '<p class="empty-state">No classes scheduled yet.</p>';
        if (deleteClassSubmit) deleteClassSubmit.disabled = true;
        return;
      }

      scheduleState.classes.forEach(entry => {
        const label = document.createElement('label');
        label.className = 'delete-option';
        label.innerHTML = `
          <input type="radio" name="classToDelete" value="${entry.class_id}">
          <div>
            <strong>${entry.day_label}</strong><br>
            <span>${entry.start_label} - ${entry.end_label}</span><br>
            <span>${entry.class_name} (Coach ${entry.instructor_name})</span>
          </div>
        `;
        deleteClassList.appendChild(label);
      });
      if (deleteClassSubmit) deleteClassSubmit.disabled = true;
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
      showLoader();
      fetch('/api/schedule/')
        .then(handleResponse)
        .then(data => {
          scheduleState.classes = data.classes || [];
          renderSchedule();
          populateDeleteList();
        })
        .catch(err => {
          console.error(err);
          showAlert('error', typeof err === 'string' ? err : 'Failed to load schedule.');
        })
        .finally(hideLoader);
    }

    if (deleteClassList) {
      deleteClassList.addEventListener('change', e => {
        if (e.target && e.target.name === 'classToDelete') {
          if (deleteClassSubmit) deleteClassSubmit.disabled = false;
          if (deleteClassError) deleteClassError.textContent = '';
        }
      });
    }

    if (editScheduleBtn && modals.options) {
      editScheduleBtn.addEventListener('click', () => openModal(modals.options, editScheduleBtn));
    }

    if (openAddClassBtn && modals.add) {
      openAddClassBtn.addEventListener('click', () => {
        closeModal(modals.options);
        openModal(modals.add, openAddClassBtn);
      });
    }

    if (openDeleteClassBtn && modals.delete) {
      openDeleteClassBtn.addEventListener('click', () => {
        closeModal(modals.options);
        populateDeleteList();
        openModal(modals.delete, openDeleteClassBtn);
      });
    }

    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal');
        closeModal(modal);
      });
    });

    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', e => {
        if (e.target === modal) {
          closeModal(modal);
        }
      });
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && activeModal) {
        closeModal(activeModal);
      }
    });

    if (addClassForm) {
      addClassForm.addEventListener('submit', e => {
        e.preventDefault();
        if (addClassError) addClassError.textContent = '';

        const formData = new FormData(addClassForm);
        const payload = {
          class_name: (formData.get('class_name') || '').trim(),
          instructor_name: (formData.get('instructor_name') || '').trim(),
          day_of_week: formData.get('day_of_week'),
          start_time: formData.get('start_time'),
          end_time: formData.get('end_time'),
        };

        const startMinutes = timeToMinutes(payload.start_time);
        const endMinutes = timeToMinutes(payload.end_time);
        if (startMinutes == null || endMinutes == null) {
          if (addClassError) addClassError.textContent = 'Please select valid times.';
          return;
        }
        if (endMinutes <= startMinutes) {
          if (addClassError) addClassError.textContent = 'End time must be later than start time.';
          return;
        }

        showLoader();
        fetch('/api/schedule/add/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify(payload),
        })
          .then(handleResponse)
          .then(() => {
            showAlert('success', 'Class added successfully.');
            closeModal(modals.add);
            fetchSchedule();
          })
          .catch(err => {
            if (addClassError) addClassError.textContent = err;
          })
          .finally(hideLoader);
      });
    }

    if (deleteClassForm) {
      deleteClassForm.addEventListener('submit', e => {
        e.preventDefault();
        if (deleteClassError) deleteClassError.textContent = '';
        const selected = deleteClassForm.querySelector('input[name="classToDelete"]:checked');
        if (!selected) {
          if (deleteClassError) deleteClassError.textContent = 'Select a class to delete.';
          return;
        }

        showLoader();
        fetch(`/api/schedule/delete/${selected.value}/`, {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': csrfToken,
          },
        })
          .then(handleResponse)
          .then(() => {
            showAlert('success', 'Class deleted successfully.');
            closeModal(modals.delete);
            fetchSchedule();
          })
          .catch(err => {
            if (deleteClassError) deleteClassError.textContent = err;
          })
          .finally(hideLoader);
      });
    }

    if (logoutButton && modals.logout) {
      logoutButton.addEventListener('click', e => {
        e.preventDefault();
        openModal(modals.logout, logoutButton);
      });

      if (logoutConfirmBtn) {
        logoutConfirmBtn.addEventListener('click', () => {
          const logoutUrl = logoutConfirmBtn.dataset.logoutUrl || logoutButton.dataset.logoutUrl;
          if (!logoutUrl) return;
          showLoader();
          window.location.href = logoutUrl;
        });
      }
    }

    fetchSchedule();
  });
})();

