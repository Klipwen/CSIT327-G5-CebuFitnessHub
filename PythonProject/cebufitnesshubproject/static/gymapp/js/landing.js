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
    
    // Clear any previous validation errors when opening modal
    clearValidationErrors();
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
  
  // Validation functions
  function validateEmail(email) {
    // Regular expression for email validation
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
  
  function sanitizeInput(input) {
    // Basic sanitization to prevent script injection
    return input.replace(/[<>&"']/g, function(c) {
      return {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#39;'
      }[c];
    });
  }
  
  function showValidationError(inputId, message) {
    var input = document.getElementById(inputId);
    if (!input) return;
    
    // Add error class to input
    input.classList.add('input-error');
    
    // Check if error message element already exists
    var errorId = inputId + '-error';
    var existingError = document.getElementById(errorId);
    
    if (existingError) {
      existingError.textContent = message;
    } else {
      // Create error message element
      var errorElement = document.createElement('div');
      errorElement.id = errorId;
      errorElement.className = 'validation-error';
      errorElement.textContent = message;
      
      // Insert after the input's parent (form-group)
      var formGroup = input.closest('.form-group');
      if (formGroup) {
        formGroup.appendChild(errorElement);
      }
    }
  }
  
  function clearValidationError(inputId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    
    // Remove error class
    input.classList.remove('input-error');
    
    // Remove error message if it exists
    var errorId = inputId + '-error';
    var errorElement = document.getElementById(errorId);
    if (errorElement) {
      errorElement.remove();
    }
  }
  
  function clearValidationErrors() {
    // Clear all validation errors
    document.querySelectorAll('.validation-error').forEach(function(el) {
      el.remove();
    });
    document.querySelectorAll('.input-error').forEach(function(el) {
      el.classList.remove('input-error');
    });
  }
  
  // Add input validation on blur
  document.addEventListener('blur', function(e) {
    if (e.target.id === 'login-email') {
      var email = e.target.value.trim();
      if (email === '') {
        clearValidationError('login-email');
      } else if (!validateEmail(email)) {
        showValidationError('login-email', 'Please enter a valid email.');
      } else {
        clearValidationError('login-email');
      }
    }
    
    if (e.target.id === 'login-password') {
      var password = e.target.value.trim();
      if (password === '') {
        showValidationError('login-password', 'Password is required.');
      } else {
        clearValidationError('login-password');
      }
    }
  }, true);

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
    
    // Clear previous validation errors
    clearValidationErrors();
    
    var email = document.getElementById('login-email').value.trim();
    var password = document.getElementById('login-password').value.trim();
    var activeTab = document.querySelector('.login-tabs .tab-btn.active');
    var role = activeTab ? activeTab.getAttribute('data-role') : 'member';
    
    // Validate and sanitize inputs
    var isValid = true;
    
    // Email validation
    if (!email) {
      showValidationError('login-email', 'Email is required.');
      isValid = false;
    } else if (!validateEmail(email)) {
      showValidationError('login-email', 'Please enter a valid email.');
      isValid = false;
    }
    
    // Password validation
    if (!password) {
      showValidationError('login-password', 'Password is required.');
      isValid = false;
    }
    
    // If validation fails, stop form submission
    if (!isValid) {
      return;
    }
    
    // Sanitize inputs
    email = sanitizeInput(email);
    password = sanitizeInput(password);
    
    // Force staff role if Staff tab is active
    if (activeTab && activeTab.classList.contains('active') && activeTab.getAttribute('data-role') === 'staff') {
      role = 'staff';
    }
    
    // Additional check: look for any staff tab that might be active
    var staffTab = document.querySelector('.login-tabs .tab-btn[data-role="staff"]');
    if (staffTab && staffTab.classList.contains('active')) {
      role = 'staff';
    }
    
    // Show loading state on button
    var submitButton = form.querySelector('.login-submit');
    var originalButtonText = submitButton.textContent;
    submitButton.textContent = 'Logging in...';
    submitButton.disabled = true;
    
    // Update the role input value
    var roleInput = document.getElementById('login-role');
    if (roleInput) {
      roleInput.value = role;
    }
    
    // Submit the existing form
    form.submit();
  });
})();



