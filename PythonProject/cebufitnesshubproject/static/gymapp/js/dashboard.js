// static/gymapp/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
  const loader = document.createElement('div');
  loader.className = 'page-loader';
  loader.innerHTML = '<div class="loader-card"><div class="loader-spinner"></div><div class="loader-text">Loading…</div></div>';
  document.body.appendChild(loader);
  const activate = () => loader.classList.add('is-active');
  const deactivate = () => loader.classList.remove('is-active');

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

  const logoutButton = document.getElementById('logoutBtn');
  if (logoutButton) {
    logoutButton.addEventListener('click', function(event) {
      event.preventDefault();
      const confirmLogout = confirm('Are you sure you want to log out?');
      if (confirmLogout) {
        activate();
        window.location.href = logoutButton.href;
      }
    });
  }
});
  