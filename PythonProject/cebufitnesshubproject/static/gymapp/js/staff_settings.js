(function () {
    'use strict';
  
    /**
     * Generates and manages a custom time picker dropdown.
     * @param {string} wrapperId - The ID of the wrapper (e.g., 'time-select-start')
     * @param {string} defaultSelectedValue - The default time (e.g., '08:00')
     */
    function initializeCustomTimePicker(wrapperId, defaultSelectedValue) {
      const wrapper = document.getElementById(wrapperId);
      if (!wrapper) return;
  
      // --- FIX: Prevent label click from opening dropdown ---
      const labelEl = wrapper.querySelector('label');
      if (labelEl) {
          labelEl.addEventListener('click', (e) => {
              e.preventDefault();
              // This stops the browser from "clicking" the button
              // when the label is clicked.
          });
      }
      // --- END FIX ---
  
  
      const trigger = wrapper.querySelector('.custom-select-trigger');
      const label = wrapper.querySelector('.custom-select-label');
      const panel = wrapper.querySelector('.custom-select-panel');
      const actionsList = wrapper.querySelector('.dropdown-actions');
  
      let currentSelectedValue = defaultSelectedValue;
  
      // --- 1. Populate the options ---
      for (let hour = 0; hour < 24; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
          const value = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
          const ampm = hour >= 12 ? 'PM' : 'AM';
          const displayHour = hour % 12 === 0 ? 12 : hour % 12;
          const displayText = `${displayHour}:${String(minute).padStart(2, '0')} ${ampm}`;
  
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'dropdown-btn btn-positive';
          button.dataset.value = value;
          button.textContent = displayText;
          button.setAttribute('role', 'menuitem');
  
          if (value === currentSelectedValue) {
            button.classList.add('is-selected-time');
          }
  
          // --- 2. Add click listener to each new option button ---
          button.addEventListener('click', () => {
            // Update the label
            label.textContent = displayText;
            currentSelectedValue = value;
  
            // Remove old selected class
            const oldSelected = actionsList.querySelector('.is-selected-time');
            if (oldSelected) oldSelected.classList.remove('is-selected-time');
  
            // Add new selected class
            button.classList.add('is-selected-time');
  
            // Close the panel
            wrapper.classList.remove('is-open');
            trigger.setAttribute('aria-expanded', 'false');
          });
  
          actionsList.appendChild(button);
        }
      }
  
      // --- 3. Add click listener to the main trigger button ---
      trigger.addEventListener('click', (e) => {
        e.stopPropagation(); // Stop click from bubbling to document
  
        // --- FIX: Check if we are in edit mode ---
        // Get the main page wrapper
        const pageWrapper = document.getElementById('settings-page-wrapper');
        // If the wrapper doesn't have '.is-editing', stop the function.
        if (!pageWrapper.classList.contains('is-editing')) {
          return; 
        }
        // --- END FIX ---
  
        // Close all other open dropdowns first
        document.querySelectorAll('.custom-select-wrapper.is-open').forEach(openWrapper => {
          if (openWrapper !== wrapper) {
            openWrapper.classList.remove('is-open');
            const otherTrigger = openWrapper.querySelector('.custom-select-trigger');
            if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
          }
        });
  
        const isOpen = wrapper.classList.toggle('is-open');
        trigger.setAttribute('aria-expanded', isOpen);
  
        // Scroll to the selected item when opening
        if (isOpen) {
          const selected = actionsList.querySelector('.is-selected-time');
          if (selected) {
            selected.scrollIntoView({ block: 'nearest' });
          }
        }
      });
    }
  
    /**
     * Initializes the main settings page functionality
     */
    function initSettingsPage() {
      const wrapper = document.getElementById('settings-page-wrapper');
      if (!wrapper) return;
  
      const btnEdit = document.getElementById('btn-edit-settings');
      const btnCancel = document.getElementById('btn-cancel-settings');
      const btnSave = document.getElementById('btn-save-settings');
  
      // --- 1. THIS IS THE FIRST FIX ---
      // Read the default values from the HTML data-attributes
      const startWrapper = document.getElementById('time-select-start');
      const endWrapper = document.getElementById('time-select-end');

      // Get the saved HH:MM value, or use the old hard-coded default as a fallback
      const defaultStartTime = startWrapper ? startWrapper.dataset.defaultValue : '08:00';
      const defaultEndTime = endWrapper ? endWrapper.dataset.defaultValue : '20:00';

      initializeCustomTimePicker('time-select-start', defaultStartTime);
      initializeCustomTimePicker('time-select-end', defaultEndTime);
      // --- END OF FIRST FIX ---

  
      // 2. Add Event Listeners for Toggling View/Edit Mode
      if (btnEdit) {
        btnEdit.addEventListener('click', () => {
          wrapper.classList.add('is-editing');
        });
      }
  
      if (btnCancel) {
        btnCancel.addEventListener('click', () => {
          wrapper.classList.remove('is-editing');
          // TODO: Add logic to reset form fields to original values
        });
      }
  
      if (btnSave) {
        btnSave.addEventListener('click', () => {
            // 1. Get all the values from the edit fields
            const data = {
                contact_number: document.getElementById('contact-number').value,
                default_fee: document.getElementById('default-fee').value,
                gym_capacity: document.getElementById('gym-capacity').value,
                
                // Get the selected values from the custom dropdowns
                peak_start: document.querySelector('#time-select-start .dropdown-btn.is-selected-time').dataset.value,
                peak_end: document.querySelector('#time-select-end .dropdown-btn.is-selected-time').dataset.value,
            };

            // 2. Get the CSRF token
            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

            // 3. Send the data to the server
            const loaderEl = document.querySelector('.page-loader');
            if (loaderEl) loaderEl.classList.add('is-active');
            fetch("/staff/settings/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    // --- 2. THIS IS THE SECOND FIX ---
                    // 4. On success, update ALL relevant fields
                    
                    // Update the simple text inputs
                    document.querySelector('#contact-number').previousElementSibling.textContent = data.contact_number;
                    document.querySelector('#default-fee').previousElementSibling.textContent = data.default_fee;
                    document.querySelector('#gym-capacity').previousElementSibling.textContent = data.gym_capacity;
                    
                    // Get the human-readable labels from the buttons we just saved
                    const startLabel = document.querySelector('#time-select-start .dropdown-btn.is-selected-time').textContent;
                    const endLabel = document.querySelector('#time-select-end .dropdown-btn.is-selected-time').textContent;
                    
                    // Update the <p> tags (view mode)
                    document.querySelector('#peak-start-trigger').previousElementSibling.textContent = startLabel;
                    document.querySelector('#peak-end-trigger').previousElementSibling.textContent = endLabel;
                    
                    // Update the <span class="custom-select-label"> (edit mode)
                    document.querySelector('#time-select-start .custom-select-label').textContent = startLabel;
                    document.querySelector('#time-select-end .custom-select-label').textContent = endLabel;
                    // --- END OF SECOND FIX ---
                    
                    // 5. Switch back to view mode
                    wrapper.classList.remove('is-editing');
                } else {
                    alert('Error saving settings: ' + result.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An unexpected error occurred. Please try again.');
            })
            .finally(() => { if (loaderEl) loaderEl.classList.remove('is-active'); });
        });
     }
  
      // 3. Add global click listener to close dropdowns
      document.addEventListener('click', (e) => {
        // If the click was inside a custom select, do nothing
        if (e.target.closest('.custom-select-wrapper')) return;
  
        // If the click was outside, close all open dropdowns
        const openSelects = document.querySelectorAll('.custom-select-wrapper.is-open');
        openSelects.forEach(wrapper => {
          wrapper.classList.remove('is-open');
          const trigger = wrapper.querySelector('.custom-select-trigger');
          if (trigger) trigger.setAttribute('aria-expanded', 'false');
        });
      });
    }
  
    // Run the initialization function when the page loads
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initSettingsPage);
    } else {
      initSettingsPage();
    }
  
  })();
  