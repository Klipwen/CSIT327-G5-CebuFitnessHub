// static/gymapp/js/dashboard.js
//not been linked to the actual project
document.addEventListener('DOMContentLoaded', function() {
    // --- Sidebar Navigation Active State ---
    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    const currentPath = window.location.pathname; // e.g., "/dashboard/" or "/dashboard/my-details/"

    sidebarLinks.forEach(link => {
        link.classList.remove('active'); // Clear existing active states

        // Construct the full path from the link's href
        const linkUrl = new URL(link.href);
        const linkPath = linkUrl.pathname.endsWith('/') ? linkUrl.pathname : linkUrl.pathname + '/'; // Ensure trailing slash consistency

        const cleanedCurrentPath = currentPath.endsWith('/') ? currentPath : currentPath + '/';

        if (cleanedCurrentPath === linkPath) {
            link.classList.add('active');
        }
    });

    // --- Apply Dynamic Width to Activity Bars ---
    document.querySelectorAll('.activity-bar').forEach(bar => {
        const percentage = bar.getAttribute('data-percentage');
        if (percentage) {
            bar.style.width = `${percentage}%`;
        }
    });

    // --- Logout Confirmation ---
    const logoutButton = document.getElementById('logoutBtn'); // Assuming your logout link has this ID
    if (logoutButton) {
        logoutButton.addEventListener('click', function(event) {
            const confirmLogout = confirm('Are you sure you want to log out?');
            if (!confirmLogout) {
                event.preventDefault(); // Prevent default link action (logout) if user cancels
            }
            // If user confirms, the browser will follow the href of the logoutButton.
            // You would link this button to a Django logout URL, e.g., <a href="{% url 'logout' %}" id="logoutBtn">Logout</a>
        });
    }

    // --- Other potential dashboard interactions (add as needed) ---
    // Example: You might want to add smooth scrolling to anchor links in the main content,
    // or interactive charts if you integrate a charting library.
});