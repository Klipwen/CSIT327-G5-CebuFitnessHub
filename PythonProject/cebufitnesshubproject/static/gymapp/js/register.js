// static/gymapp/js/register.js

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById("registrationModal");
    // Select all elements that should open the modal
    const openModalBtns = document.querySelectorAll(".register-link");
    const closeModalBtn = document.querySelector(".modal-content .close-button");

    // Function to open the modal
    if (openModalBtns.length > 0) {
        openModalBtns.forEach(btn => {
            btn.addEventListener('click', (event) => {
                event.preventDefault(); // Prevents the link from navigating
                modal.style.display = "flex"; // Use flex to center the modal
                document.body.style.overflow = 'hidden'; // Prevent background scrolling
            });
        });
    }

    // Function to close the modal
    const close = () => {
        modal.style.display = "none";
        document.body.style.overflow = 'auto'; // Restore background scrolling
    };

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', close);
    }
    
    // Also attach close function to the "Back to Home" link inside the modal
    const backToHomeLink = document.querySelector('.back-to-home-link');
    if (backToHomeLink) {
        backToHomeLink.addEventListener('click', close);
    }

    // Close the modal if the user clicks anywhere outside of the modal content (backdrop click)
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            backToHomeLink.click();
        }
    });

    // Password visibility toggle
        // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.toggle-password');

    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const targetId = toggle.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);

            // Find the eye / eye-slash icons inside this toggle
            const eyeIcon = toggle.querySelector('.eye-icon');
            const eyeSlashIcon = toggle.querySelector('.eye-slash-icon');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';   // Show letters
                if (eyeIcon && eyeSlashIcon) {
                    eyeIcon.classList.add('hidden');     // hide eye
                    eyeSlashIcon.classList.remove('hidden'); // show eye-slash
                }
            } else {
                passwordInput.type = 'password';  // Hide letters
                if (eyeIcon && eyeSlashIcon) {
                    eyeIcon.classList.remove('hidden');   // show eye
                    eyeSlashIcon.classList.add('hidden'); // hide eye-slash
                }
            }
        });
    });

});
