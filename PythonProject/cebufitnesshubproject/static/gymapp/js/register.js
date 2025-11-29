// static/gymapp/js/register.js

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById("registrationModal");
    const openModalBtns = document.querySelectorAll(".register-link");
    // const registrationForm = document.getElementById('registrationForm'); // No longer needed for validation logic

    // Modal open/close logic
    if (openModalBtns.length > 0) {
        openModalBtns.forEach(btn => {
            btn.addEventListener('click', (event) => {
                event.preventDefault();
                modal.style.display = "flex";
                document.body.style.overflow = 'hidden';
            });
        });
    }

    const close = () => {
        modal.style.display = "none";
        document.body.style.overflow = 'auto';
        // No client-side errors to clear if we're not displaying them
    };
    
    const backToHomeLink = document.querySelector('.back-to-home-link');
    if (backToHomeLink) {
        backToHomeLink.addEventListener('click', close);
    }

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            event.stopPropagation(); //Disable closing when clicking outside the modal
        }
    });

    // Password visibility toggle (remains unchanged)
    const passwordToggles = document.querySelectorAll('.toggle-password');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const targetId = toggle.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);

            const eyeIcon = toggle.querySelector('.eye-icon');
            const eyeSlashIcon = toggle.querySelector('.eye-slash-icon');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';   
                if (eyeIcon && eyeSlashIcon) {
                    eyeIcon.classList.add('hidden');     
                    eyeSlashIcon.classList.remove('hidden'); 
                }
            } else {
                passwordInput.type = 'password';  
                if (eyeIcon && eyeSlashIcon) {
                    eyeIcon.classList.remove('hidden');   
                    eyeSlashIcon.classList.add('hidden'); 
                }
            }
        });
    });

	// Removed all client-side validation logic from here.
	// The form will now simply submit, and Django's server-side
	// validation (handled in views.py and forms.py) will process it.
	// Errors will be displayed on the page refresh by Django.
});