// static/gymapp/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // --- Logout Confirmation ---
    const logoutButton = document.getElementById('logoutBtn');
  
    if (logoutButton) {
      logoutButton.addEventListener('click', function(event) {
        // This stops the link from navigating immediately
        event.preventDefault();
  
        const confirmLogout = confirm('Are you sure you want to log out?');
  
        if (confirmLogout) {
          // If user clicks "OK", manually follow the link
          window.location.href = logoutButton.href;
        }
        // If user clicks "Cancel", do nothing.
      });
    }
  });
  