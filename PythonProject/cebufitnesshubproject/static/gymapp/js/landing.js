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

  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-open-login]');
    if (opener) {
      e.preventDefault();
      var role = opener.getAttribute('data-open-login') || 'member';
      openModal(role);
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeModal();
  });

  // Handle form submission
  document.addEventListener('submit', function (e) {
    var form = e.target.closest('.login-form');
    if (!form) return;
    
    // Always prevent default first
    e.preventDefault();
    
    var email = document.getElementById('login-email').value;
    var password = document.getElementById('login-password').value;
    var activeTab = document.querySelector('.login-tabs .tab-btn.active');
    var role = activeTab ? activeTab.getAttribute('data-role') : 'member';
    
    if (!email || !password) {
      alert('Please fill in all fields.');
      return;
    }
    
    // Force staff role if Staff tab is active
    if (activeTab && activeTab.classList.contains('active') && activeTab.getAttribute('data-role') === 'staff') {
      role = 'staff';
    }
    
    // Additional check: look for any staff tab that might be active
    var staffTab = document.querySelector('.login-tabs .tab-btn[data-role="staff"]');
    if (staffTab && staffTab.classList.contains('active')) {
      role = 'staff';
    }
    
    // Determine the correct URL based on role
    var actionUrl;
    
    if (role === 'staff') {
      actionUrl = '/staff_dashboard/';
    } else {
      actionUrl = '/dashboard/';
    }
    
    // Create a new form to submit to the correct URL
    var newForm = document.createElement('form');
    newForm.method = 'POST';
    newForm.action = actionUrl;
    newForm.style.display = 'none';
    
    // Add CSRF token
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
      var csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      csrfInput.value = csrfToken.value;
      newForm.appendChild(csrfInput);
    }
    
    // Add email and password
    var emailInput = document.createElement('input');
    emailInput.type = 'hidden';
    emailInput.name = 'email';
    emailInput.value = email;
    newForm.appendChild(emailInput);
    
    var passwordInput = document.createElement('input');
    passwordInput.type = 'hidden';
    passwordInput.name = 'password';
    passwordInput.value = password;
    newForm.appendChild(passwordInput);
    
    // Add form to body and submit
    document.body.appendChild(newForm);
    newForm.submit();
  });
})();



