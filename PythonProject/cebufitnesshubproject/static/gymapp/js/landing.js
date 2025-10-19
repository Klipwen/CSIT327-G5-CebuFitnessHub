// landing.js

(function () {
  // Expose functions globally that need to be called from the Django template
  window.selectTab = function(role) {
    var buttons = document.querySelectorAll('.login-tabs .tab-btn');
    var loginForm = document.getElementById('login-form'); // Get the form

    buttons.forEach(function (btn) {
      var isActive = btn.getAttribute('data-role') === role;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', String(isActive));
    });

    // **CRITICAL:** Update the form's action attribute when the tab changes
    if (loginForm) {
      if (role === 'staff') {
        loginForm.action = '/staff-login/'; // Assuming your staff login URL is this
      } else {
        loginForm.action = '/login/'; // Your member login URL
      }
    }
  };

  window.openModal = function(defaultRole) {
    var backdrop = document.getElementById('login-backdrop');
    if (!backdrop) return;
    if (defaultRole) {
      window.selectTab(defaultRole); // Use window.selectTab to also set form action
    } else {
      // If no defaultRole, ensure the member tab is selected by default
      window.selectTab('member');
    }
    backdrop.classList.add('is-open');
    backdrop.removeAttribute('aria-hidden');
    document.body.style.overflow = 'hidden';
  };

  window.closeModal = function() {
    var backdrop = document.getElementById('login-backdrop');
    if (!backdrop) return;
    backdrop.classList.remove('is-open');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    // Clear any messages when modal closes
    const messagesContainer = document.getElementById('login-messages-container');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
    // Clear form inputs
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    if (emailInput) emailInput.value = '';
    if (passwordInput) passwordInput.value = '';

    // Clear inline errors
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');
    if (emailError) emailError.textContent = '';
    if (passwordError) passwordError.textContent = '';
  };

  function togglePasswordVisibility() {
    var input = document.getElementById('login-password');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
  }

  document.addEventListener('click', function (e) {
    // Tabs
    var tabBtn = e.target.closest('.login-tabs .tab-btn');
    if (tabBtn) {
      window.selectTab(tabBtn.getAttribute('data-role'));
      return;
    }

    // Openers (within join section cards)
    // The [data-open-login] handler below now covers these.
    // Keeping these specific checks for clarity if needed, but the general one is preferred.
    if (e.target.closest('.card.member-card .btn') && !e.target.closest('.btn-outline')) {
      e.preventDefault();
      window.openModal('member');
      return;
    }
    if (e.target.closest('.card.staff-card .btn-staff')) {
      e.preventDefault();
      window.openModal('staff');
      return;
    }

    // Close button
    if (e.target.closest('.login-close')) {
      e.preventDefault();
      window.closeModal();
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
      window.closeModal();
    }
  });

  // General handler for any button with data-open-login
  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-open-login]');
    if (opener) {
      e.preventDefault();
      var role = opener.getAttribute('data-open-login') || 'member';
      window.openModal(role);
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') window.closeModal();
  });

  // **IMPORTANT: REMOVE THE FOLLOWING BLOCK**
  // document.addEventListener('submit', function (e) { ... });
  // This block is no longer needed as the form will submit naturally.

})();