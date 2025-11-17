// static/gymapp/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
  const loader = document.createElement('div');
  loader.className = 'page-loader';
  loader.innerHTML = '<div class="loader-card"><div class="loader-spinner"></div><div class="loader-text">Loading…</div></div>';
  document.body.appendChild(loader);
  const activate = () => loader.classList.add('is-active');

  const enableAnchorLoader = document.body.dataset.enableAnchorLoader === 'true';
  const links = document.querySelectorAll('.side-nav .nav-item, .navbar a');
  links.forEach(a => {
    a.addEventListener('click', e => {
      const href = a.getAttribute('href') || '';
      if (a.id === 'logoutBtn') return;
      if (!enableAnchorLoader && href.startsWith('#')) return;
      if (a.classList.contains('active')) return;
      activate();
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
  