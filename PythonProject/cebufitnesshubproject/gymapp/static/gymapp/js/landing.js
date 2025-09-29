(function () {
  function selectTab(role) {
    var buttons = document.querySelectorAll('.login-tabs .tab-btn');
    buttons.forEach(function (btn) {
      var isActive = btn.getAttribute('data-role') === role;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', String(isActive));
    });
  }

  function openModal(defaultRole) {
    var backdrop = document.getElementById('login-backdrop');
    if (!backdrop) return;
    if (defaultRole) selectTab(defaultRole);
    backdrop.classList.add('is-open');
    backdrop.removeAttribute('aria-hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    var backdrop = document.getElementById('login-backdrop');
    if (!backdrop) return;
    backdrop.classList.remove('is-open');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function togglePasswordVisibility() {
    var input = document.getElementById('login-password');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
  }

  document.addEventListener('click', function (e) {
    // Tabs
    var tabBtn = e.target.closest('.login-tabs .tab-btn');
    if (tabBtn) {
      selectTab(tabBtn.getAttribute('data-role'));
      return;
    }

    // Openers (within join section cards)
    if (e.target.closest('.card.member-card .btn') && !e.target.closest('.btn-outline')) {
      e.preventDefault();
      openModal('member');
      return;
    }
    if (e.target.closest('.card.staff-card .btn-staff')) {
      e.preventDefault();
      openModal('staff');
      return;
    }

    // Close button
    if (e.target.closest('.login-close')) {
      e.preventDefault();
      closeModal();
      return;
    }

    // Password toggle
    if (e.target.closest('.toggle-password')) {
      e.preventDefault();
      togglePasswordVisibility();
      return;
    }

    // Backdrop click
    var backdrop = document.getElementById('login-backdrop');
    if (backdrop && e.target === backdrop) {
      closeModal();
    }
  });

  // Header Join button should just navigate to join section (default behavior already scrolls).
  // If there will be a green Login button in header later, wire with data attribute:
  // <a class="login-btn" data-open-login="member">Login</a>
  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-open-login]');
    if (opener) {
      e.preventDefault();
      var role = opener.getAttribute('data-open-login') || 'member';
      openModal(role);
    }
  });

  // Escape closes modal
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });
})();


