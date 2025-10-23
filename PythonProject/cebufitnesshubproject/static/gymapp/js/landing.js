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
        // NOTE: The submit handler logic in this file will override this action,
        // but it's good practice to keep it for non-JS or if logic changes.
        // We will rely on the submit handler's AJAX URL.
        loginForm.action = '/login/'; 
      } else {
        loginForm.action = '/login/'; // Your member login URL
      }
    }

    // Hide register CTA when Staff tab is active; show for Member
    var registerCta = document.querySelector('.register-cta');
    if (registerCta) {
      registerCta.style.display = (role === 'staff') ? 'none' : '';
    }
  };

  // Prevent hash-only navigation for anchors like href="#"
  document.addEventListener('click', function (e) {
    var hashAnchor = e.target.closest('a[href="#"]');
    if (hashAnchor) {
      e.preventDefault();
    }
  });

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
    
    // Clear any previous validation errors when opening modal
    clearValidationErrors();
  }

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
    
    // Also clear validation classes
    clearValidationErrors();
  };

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
      
      // Insert after the input's parent wrapper (input-wrapper)
      var inputWrapper = input.closest('.input-wrapper');
      if (inputWrapper) {
          inputWrapper.insertAdjacentElement('afterend', errorElement);
      } else {
          // Fallback to form-group
          var formGroup = input.closest('.form-group');
          if (formGroup) {
            formGroup.appendChild(errorElement);
          }
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
        // Only show error if they blurred without typing
        // Re-validating on blur for password can be annoying
      } else {
        clearValidationError('login-password');
      }
    }
  }, true); // Use capture phase

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
    // This will now use the AJAX handler from the other script (if present)
    // or submit normally to the URL defined in form.action
    
    // Re-enabling the default submit behavior as intended by feat/staff-login-validation
    form.submit();
  });
  
  // Refresh landing page only when restored from BFCache
  var hasReloadedOnBFCache = false;
  window.addEventListener('pageshow', function (event) {
    try {
      var isLanding = window.location.pathname === '/';
      if (event.persisted && isLanding && !hasReloadedOnBFCache) {
        hasReloadedOnBFCache = true;
        window.location.reload();
        return;
      }
      // Reset login button state defensively
      var submitButton = document.querySelector('.login-form .login-submit');
      if (submitButton) {
        submitButton.textContent = 'Log in';
        submitButton.disabled = false;
      }
    } catch (e) {
      // No-op
    }
  });

})();

// Utility helpers
function byId(id) { return document.getElementById(id); }
function qs(sel, root = document) { return root.querySelector(sel); }
function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

// Modal open function (assumed existing elsewhere)
window.openModal = window.openModal || function(defaultTab = 'member') {
  const modal = byId('loginModal');
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  selectTab(defaultTab);
};

// Tab selection logic
function selectTab(role) {
  const tabs = qsa('.tab');
  const forms = qsa('.login-form');
  const hiddenRoleInput = qs('input[name="login-role"]');
  const registerCTA = qs('.register-cta');

  tabs.forEach(t => t.classList.toggle('active', t.dataset.role === role));
  forms.forEach(f => f.classList.toggle('active', f.dataset.role === role));

  if (hiddenRoleInput) hiddenRoleInput.value = role;

  // Hide register CTA for staff; show for member
  if (registerCTA) {
    registerCTA.style.display = role === 'staff' ? 'none' : '';
  }
}

// Initialize default tab on modal open based on active tab or hidden input
function initModalState() {
  const activeTab = qs('.tab.active');
  const hiddenRoleInput = qs('input[name="login-role"]');
  const role = activeTab ? activeTab.dataset.role : (hiddenRoleInput ? hiddenRoleInput.value : 'member');
  selectTab(role || 'member');
}

// Prevent hash-only navigation used to open modals
// This stops `/#` jumps due to anchors like href="#"
document.addEventListener('click', function(e) {
  const anchor = e.target.closest('a[href="#"]');
  if (anchor) {
    e.preventDefault();
  }
});

// Refresh only on BFCache restores to avoid stale "Logging in..." state
window.addEventListener('pageshow', function(event) {
  if (event.persisted) {
    window.location.reload();
  }
});

// On initial load, if URL hash is #join, open login modal
document.addEventListener('DOMContentLoaded', function() {
  try {
    if (window.location.hash === '#join') {
      // Default to member tab when deep-linking to login modal
      window.openModal('member');
    }
  } catch (err) {
    // Swallow errors to avoid breaking landing page
    console.error('Error opening modal from hash:', err);
  }
});

// Form validation and submission handling
(function() {
  const loginForm = byId('loginForm');
  if (!loginForm) return;

  const emailInput = byId('login-email');
  const passwordInput = byId('login-password');
  const submitBtn = byId('login-submit');

  function setLoading(isLoading) {
    if (!submitBtn) return;
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? 'Logging in...' : 'Login';
  }

  function showInlineError(message) {
    const errorEl = byId('login-error');
    if (!errorEl) return;
    errorEl.textContent = message || '';
    errorEl.style.display = message ? 'block' : 'none';
  }

  function sanitize(value) {
    return String(value || '').trim();
  }

  function getActiveRole() {
    const activeTab = qs('.tab.active');
    return activeTab ? activeTab.dataset.role : 'member';
  }

  function isValidEmail(email) {
    return /\S+@\S+\.\S+/.test(email);
  }

  loginForm.addEventListener('submit', function(e) {
    showInlineError('');

    const email = sanitize(emailInput && emailInput.value);
    const password = sanitize(passwordInput && passwordInput.value);

    // Client-side validation
    if (!email || !isValidEmail(email)) {
      e.preventDefault();
      showInlineError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      e.preventDefault();
      showInlineError('Please enter your password.');
      return;
    }

    // Update hidden role input before submission
    const hiddenRoleInput = qs('input[name="login-role"]');
    const role = getActiveRole();
    if (hiddenRoleInput) hiddenRoleInput.value = role;

    // Show loading state; allow default form submit
    setLoading(true);
    // Expect server-side (views.member_login) to validate role and return JSON errors or redirect
  }, false);
})();