(function () {
  var sections = document.querySelectorAll('[data-section]');
  
  sections.forEach(function (section) {
    var shouldFail = section.dataset.section === 'approvals' ? false : false;
    var fallback = section.querySelector('.fallback');
    if (fallback) {
      fallback.style.display = shouldFail ? 'block' : 'none';
    }
  });

  var openBtn = document.getElementById('open-logout');
  var backdrop = document.getElementById('logout-backdrop');
  var cancelBtn = document.getElementById('logout-cancel');
  var closeBtn = document.getElementById('logout-close');

  function openModal() {
    if (backdrop) {
      backdrop.classList.add('is-open');
      backdrop.setAttribute('aria-hidden', 'false');
    }
  }

  function closeModal() {
    if (backdrop) {
      backdrop.classList.remove('is-open');
      backdrop.setAttribute('aria-hidden', 'true');
    }
  }

  if (openBtn) {
    openBtn.addEventListener('click', function (e) {
      e.preventDefault();
      openModal();
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', function () {
      closeModal();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      closeModal();
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', function (e) {
      if (e.target === backdrop) closeModal();
    });
  }
})();
