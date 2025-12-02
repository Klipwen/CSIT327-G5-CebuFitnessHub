// static/gymapp/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
  const loader = document.createElement('div');
  loader.className = 'page-loader';
  loader.innerHTML = '<div class="loader-card"><div class="loader-spinner"></div><div class="loader-text">Loading…</div></div>';
  document.body.appendChild(loader);
  const activate = () => loader.classList.add('is-active');
  const deactivate = () => loader.classList.remove('is-active');
  let lastFocusedElement = null;

  function getFocusableElements(modal) {
    if (!modal) return [];
    return modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
  }

  function openModal(modal, triggerElement) {
    if (!modal) return;

    lastFocusedElement = triggerElement || null;
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');

    const focusableElements = getFocusableElements(modal);
    focusableElements.forEach(el => el.setAttribute('tabindex', '0'));
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }

    modal.addEventListener('keydown', trapFocus);
  }

  function closeModal(modal) {
    if (!modal) return;

    const form = modal.querySelector('form');
    if (form) form.reset();

    const focusableElements = getFocusableElements(modal);
    focusableElements.forEach(el => el.setAttribute('tabindex', '-1'));

    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    modal.removeEventListener('keydown', trapFocus);

    if (lastFocusedElement) {
      lastFocusedElement.focus();
      lastFocusedElement = null;
    }
  }

  function trapFocus(e) {
    if (e.key !== 'Tab') return;

    const modal = e.currentTarget;
    const focusableElements = getFocusableElements(modal);
    if (!focusableElements.length) return;

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstFocusable) {
      e.preventDefault();
      lastFocusable.focus();
    } else if (!e.shiftKey && document.activeElement === lastFocusable) {
      e.preventDefault();
      firstFocusable.focus();
    }
  }

  // Function to update active navigation state based on hash or current page
  function updateActiveNavigation(hash) {
    const navItems = document.querySelectorAll('.side-nav .nav-item');
    navItems.forEach(item => {
      item.classList.remove('active');
    });

    // Check if we're on the settings page
    const currentPath = window.location.pathname;
    const isSettingsPage = currentPath.includes('/staff/settings/');
    
    if (isSettingsPage) {
      // Highlight Settings button if on settings page
      const settingsNavItem = document.querySelector('.side-nav .nav-item[href*="staff/settings"], .side-nav .nav-item[href="#settings"]');
      if (settingsNavItem) {
        settingsNavItem.classList.add('active');
      }
      return;
    }

    // Map hash to navigation item (for dashboard page)
    let targetHash = hash || '#overview-section';
    
    // If hash is empty or just '#', default to overview
    if (!hash || hash === '#' || hash === '') {
      targetHash = '#overview-section';
    }

    // Find the navigation item that matches the hash
    const activeNavItem = document.querySelector(`.side-nav .nav-item[href="${targetHash}"]`);
    if (activeNavItem) {
      activeNavItem.classList.add('active');
    } else {
      // Fallback: if no match found, activate overview
      const overviewNavItem = document.querySelector('.side-nav .nav-item[href="#overview-section"]');
      if (overviewNavItem) {
        overviewNavItem.classList.add('active');
      }
    }
  }

  // Update active navigation on page load based on URL hash or current page
  const currentHash = window.location.hash;
  const currentPath = window.location.pathname;
  const isSettingsPage = currentPath.includes('/staff/settings/');
  
  if (isSettingsPage) {
    // On settings page, highlight Settings button
    updateActiveNavigation();
  } else if (currentHash) {
    // Wait a bit for the page to fully load, then update and scroll
    setTimeout(() => {
      updateActiveNavigation(currentHash);
      const targetId = currentHash.substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  } else {
    // No hash, default to overview
    updateActiveNavigation('#overview-section');
  }

  // Listen for hash changes (when user navigates via browser back/forward)
  window.addEventListener('hashchange', function() {
    updateActiveNavigation(window.location.hash);
  });

  const enableAnchorLoader = document.body.dataset.enableAnchorLoader === 'true';
  const useLogoutModal = document.body.dataset.useLogoutModal === 'true';
  const links = document.querySelectorAll('.side-nav .nav-item, .navbar a');
  links.forEach(a => {
    a.addEventListener('click', e => {
      const href = a.getAttribute('href') || '';
      if (a.id === 'logoutBtn') return;
      if (!enableAnchorLoader && href.startsWith('#')) return;
      
      // If it's an anchor link, show loader and hide it after navigation completes
      if (href.startsWith('#')) {
        e.preventDefault(); // Prevent default anchor navigation
        activate();
        
        // Update active navigation immediately
        updateActiveNavigation(href);
        
        // Get the target element
        const targetId = href.substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
          // Update URL hash without triggering scroll
          if (history.pushState) {
            history.pushState(null, null, href);
          } else {
            window.location.hash = href;
          }
          
          // Scroll to the element smoothly
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          
          // Hide loader after scroll animation completes (typically 500-600ms)
          setTimeout(() => {
            deactivate();
          }, 700);
        } else {
          // If element not found, hide loader immediately
          deactivate();
        }
      } else {
        // For non-anchor links, just activate (page will reload)
        activate();
      }
    });
  });

  const forms = document.querySelectorAll('form');
  forms.forEach(f => {
    f.addEventListener('submit', () => activate());
  });

  // ============================================================
  // GENERIC MODAL CLOSE LOGIC (Handles ALL modals)
  // ============================================================
  
  // 1. Handle [data-close] buttons (The "X" or "Cancel" buttons)
  document.querySelectorAll('[data-close]').forEach(el => {
    el.addEventListener('click', e => {
      const parentModal = e.target.closest('.modal');
      closeModal(parentModal);
    });
  });

  // 2. Handle Backdrop Clicks (Clicking outside the box)
  document.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', e => {
      if (e.target === m) {
        // EXCEPTION: Do not close these specific notification modals on backdrop click
        if (m.id === 'modalStatusSnapshot' || m.id === 'modalFriendlyReminder' || m.id === 'modalUrgentAlert') {
            return; // Do nothing
        }
        closeModal(m);
      }
    });
  });
  // ============================================================

  const logoutButton = document.getElementById('logoutBtn');
  const logoutModal = document.getElementById('modalLogout');
  const logoutConfirmBtn = document.getElementById('btnConfirmLogout');

  if (logoutButton && useLogoutModal && logoutModal) {
    logoutButton.addEventListener('click', e => {
      e.preventDefault();
      openModal(logoutModal, logoutButton);
    });

    if (logoutConfirmBtn) {
      logoutConfirmBtn.addEventListener('click', () => {
        const logoutUrl =
          logoutConfirmBtn.dataset.logoutUrl || logoutButton.dataset.logoutUrl;
        if (!logoutUrl) return;
        activate();
        window.location.href = logoutUrl;
      });
    }

    //Old code for modal close buttons
    /*const modalCloseButtons = logoutModal.querySelectorAll('[data-close]');
    modalCloseButtons.forEach(btn => {
      btn.addEventListener('click', () => closeModal(logoutModal));
    });

    logoutModal.addEventListener('click', e => {
      if (e.target === logoutModal) {
        closeModal(logoutModal);
      }
    }); */
  } else if (logoutButton) {
    logoutButton.addEventListener('click', event => {
      event.preventDefault();
      const confirmLogout = confirm('Are you sure you want to log out?');
      if (confirmLogout) {
        const logoutUrl = logoutButton.dataset.logoutUrl || logoutButton.href;
        if (!logoutUrl) return;
        activate();
        window.location.href = logoutUrl;
      }
    });
  }

  // =====================================================
  // NOTIFICATION MODAL LOGIC
  // =====================================================
  const shouldShowModal = document.body.dataset.showModal === 'true'; // NEW CHECK
  
  if (shouldShowModal) {
      const isExpired = document.body.dataset.isExpired === 'true';
      const hasBalance = document.body.dataset.hasBalance === 'true';
      const daysUntilDue = parseInt(document.body.dataset.daysUntilDue || '999');

      // 1. Urgent (Overdue)
      if (isExpired && hasBalance) {
          const modal = document.getElementById('modalUrgentAlert');
          if (modal) openModal(modal);
      } 
      // 2. Friendly Reminder (Due within 7 days)
      else if (hasBalance && daysUntilDue <= 7 && daysUntilDue >= 0) {
          const modal = document.getElementById('modalFriendlyReminder');
          if (modal) openModal(modal);
      }
      // 3. Status Snapshot (Default Welcome)
      else if (hasBalance) { 
          const modal = document.getElementById('modalStatusSnapshot');
          if (modal) openModal(modal);
      }
  }
  
});
  