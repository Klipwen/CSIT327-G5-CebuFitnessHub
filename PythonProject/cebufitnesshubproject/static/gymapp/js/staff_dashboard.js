(function () {
  'use strict';

  // ====================================================================
  // VARIABLES
  // ====================================================================

  // Keeps track of the dropdown's original wrapper
  let originalWrapper = null;

  // Keeps track of the element that triggered the modal (to restore focus)
  let lastFocusedElement;


  // ====================================================================
  // CORE MODAL FRAMEWORK (Accessible and Generic)
  // ====================================================================

  function openModal(modal, triggerElement) {
    if (!modal) return;

    lastFocusedElement = triggerElement;
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');

    // Find all focusable elements and enable them
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusableElements.forEach(el => el.setAttribute('tabindex', '0'));

    // Focus first focusable element
    const firstFocusable = focusableElements[0];
    if (firstFocusable) firstFocusable.focus();

    modal.addEventListener('keydown', trapFocus);
  }

  function closeModal(modal) {
    if (!modal) return;

    // Reset form fields inside the modal if any
    const form = modal.querySelector('form');
    if (form) form.reset();

    // Clear the read-only textarea for the approval modal
    const approvalTextarea = modal.querySelector('#approval-reason-text');
    if (approvalTextarea) approvalTextarea.value = '';

    // --- ADDED ---
    // Clear the read-only member name in the Log Payment modal
    const logPaymentMember = modal.querySelector('#log-member-name');
    if (logPaymentMember) logPaymentMember.value = '';
    // --- END ADDED ---

    // --- ADDED: Clear Freeze Modal fields on close ---
    const freezeMemberName = modal.querySelector('#freeze-member-name');
    const freezeReason = modal.querySelector('#freeze-reason');
    if (freezeMemberName) freezeMemberName.value = '';
    if (freezeReason) freezeReason.value = '';
    // --- END ADDED ---

    // --- ADDED: Clear Check-In Modal fields ---
    const checkinMemberName = modal.querySelector('#checkin-member-name');
    const checkinMemberStatus = modal.querySelector('#checkin-member-status');
    if (checkinMemberName) checkinMemberName.value = '';
    if (checkinMemberStatus) checkinMemberStatus.value = '';
    // --- END ADDED ---

    // --- NEW: Clear Unfreeze Modal fields on close ---
    const unfreezeMemberName = modal.querySelector('#unfreeze-member-name');
    const unfreezeReason = modal.querySelector('#unfreeze-reason');
    if (unfreezeMemberName) unfreezeMemberName.value = '';
    if (unfreezeReason) unfreezeReason.value = '';
    // --- END NEW ---

    // --- NEW: Clear Activate Membership Modal fields ---
    const activateMemberName = modal.querySelector('#activate-member-name');
    const activateAmount = modal.querySelector('#activate-amount');
    if (activateMemberName) activateMemberName.value = '';
    if (activateAmount) activateAmount.value = '';
    // --- END NEW ---

    // --- MODIFIED: Reset View/Edit modal to View mode AND RESET TABS on close ---
    if (modal.id === 'modalViewDetails') {
        modal.classList.remove('is-editing');

        // --- PASTE THE TAB RESET CODE HERE ---
        modal.querySelectorAll('.modal-tab-btn').forEach((btn, index) => {
            // Find the pane that corresponds to the button
            const pane = modal.querySelector(`#tab-${btn.dataset.tab}`); 
            
            if (index === 0) {
                // This is the first tab, make it active
                btn.classList.add('is-active');
                btn.setAttribute('aria-selected', 'true');
                btn.setAttribute('tabindex', '0');
                if (pane) pane.classList.add('is-active');
            } else {
                // This is not the first tab, make it inactive
                btn.classList.remove('is-active');
                btn.setAttribute('aria-selected', 'false');
                btn.setAttribute('tabindex', '-1');
                if (pane) pane.classList.remove('is-active');
            }
        });
        // --- END OF PASTED CODE ---
    }
    // --- END MODIFIED ---

    // Make all modal elements unfocusable
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusableElements.forEach(el => el.setAttribute('tabindex', '-1'));

    // Hide modal
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    modal.removeEventListener('keydown', trapFocus);

    // Restore focus to the element that opened the modal
    if (lastFocusedElement) lastFocusedElement.focus();
  }

  function trapFocus(e) {
    if (e.key !== 'Tab') return;

    const modal = e.currentTarget;
    const focusableElements = Array.from(
      modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
    ).filter(el => el.getAttribute('tabindex') !== '-1');

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey) {
      // Shift + Tab → wrap to last element
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      // Tab → wrap to first element
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  }


  // ====================================================================
  // MEMBER MANAGEMENT FUNCTIONS
  // ====================================================================

  function handleMemberFilterChange(selectedValue) {
    const searchGroup = document.getElementById('member-search-group');
    if (!searchGroup) return;

    const activeTbody = document.getElementById('member-management-tbody');
    const pendingTbody = document.getElementById('member-management-tbody-pending');
    const frozenTbody = document.getElementById('member-management-tbody-frozen');

    // Hide all sections
    [activeTbody, pendingTbody, frozenTbody].forEach(tbody => {
      if (tbody) tbody.style.display = 'none';
    });

    // Show the selected section
    const searchInput = document.getElementById('member-search-input');
    if (selectedValue === 'active' && activeTbody) {
      activeTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'flex';
    } else if (selectedValue === 'pending' && pendingTbody) {
      pendingTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'none';
      if (searchInput) searchInput.value = '';
    } else if (selectedValue === 'frozen' && frozenTbody) {
      frozenTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'none';
      if (searchInput) searchInput.value = '';
    }
  }


  // ====================================================================
  // FILTER DROPDOWN INITIALIZATION
  // ====================================================================

  function initializeFilterDropdown() {
    const component = document.getElementById('member-filter-component');
    if (!component) return;

    const trigger = component.querySelector('.member-filter-trigger');
    const label = component.querySelector('#member-filter-label');
    const panel = component.querySelector('.filter-dropdown-panel');
    const options = component.querySelectorAll('.dropdown-btn[data-value]');

    // Set initial state
    const defaultOption = component.querySelector('.dropdown-btn[data-value="active"]');
    if (defaultOption) defaultOption.style.display = 'none';

    function openMenu() {
      panel.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
    }

    function closeMenu() {
      panel.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', e => {
      e.stopPropagation();

      if (panel.classList.contains('is-open')) {
        closeMenu();
      } else {
        // Close any open action dropdown first
        const openActionDropdown = document.querySelector('.action-dropdown.is-open');
        if (openActionDropdown) {
          openActionDropdown.classList.remove('is-open');
          const oldTrigger = openActionDropdown.closest('.action-menu-wrapper')?.querySelector('.action-menu-btn');
          if (oldTrigger) oldTrigger.setAttribute('aria-expanded', 'false');
        }
        openMenu();
      }
    });

    options.forEach(option => {
      option.addEventListener('click', function () {
        const selectedValue = option.dataset.value;
        const selectedLabel = option.dataset.label;

        options.forEach(btn => (btn.style.display = 'block'));
        option.style.display = 'none';
        label.textContent = selectedLabel;

        handleMemberFilterChange(selectedValue);
        closeMenu();
      });
    });

    document.addEventListener('click', e => {
      if (!component.contains(e.target) && panel.classList.contains('is-open')) {
        closeMenu();
      }
    });
  }


  // ====================================================================
  // ACTION DROPDOWN LOGIC
  // ====================================================================
// --- MODIFIED: Function now accepts the 'modals' object from init()
  function initializeActionDropdowns(modals) {
    document.body.addEventListener('click', function (e) {
      const triggerButton = e.target.closest('.action-menu-btn');
      const openDropdown = document.querySelector('.action-dropdown.is-open');

      // Case 1: Clicked the trigger button
      if (triggerButton) {
        e.preventDefault();

        const wrapper = triggerButton.closest('.action-menu-wrapper');
        const dropdown = wrapper.querySelector('.action-dropdown');
        if (!dropdown) return;

        // Toggle current dropdown
        if (dropdown.classList.contains('is-open')) {
          dropdown.classList.remove('is-open');
          triggerButton.setAttribute('aria-expanded', 'false');
          if (originalWrapper) {
            originalWrapper.appendChild(dropdown);
            dropdown.classList.remove('is-portaled');
            originalWrapper = null;
          }
          return;
        }

        // Close previously open dropdown
        if (openDropdown) {
          openDropdown.classList.remove('is-open');
          const oldTrigger = document.querySelector('.action-menu-btn[aria-expanded="true"]');
          if (oldTrigger) oldTrigger.setAttribute('aria-expanded', 'false');
          if (originalWrapper) {
            originalWrapper.appendChild(openDropdown);
            openDropdown.classList.remove('is-portaled');
          }
        }

        // Portal the dropdown for proper layering
        originalWrapper = wrapper;
        document.body.appendChild(dropdown);
        dropdown.classList.add('is-portaled', 'is-open');
        triggerButton.setAttribute('aria-expanded', 'true');
        positionDropdown(dropdown, triggerButton);
        return;
      }

      // Case 2: Clicked inside an open dropdown → close it
      if (openDropdown && e.target.closest('.action-dropdown.is-open')) {
        const clickedButton = e.target.closest('.dropdown-btn');
        // --- MODIFIED ---
        // Find the trigger *before* checking which button was clicked
        const trigger = document.querySelector('.action-menu-btn[aria-expanded="true"]');
        // --- END MODIFIED ---
        //ADD for reading in the html
        const row = trigger.closest('tr'); // Get the row

        if (clickedButton && clickedButton.textContent.trim() === 'Log Payment') {
          e.preventDefault(); // Stop the click from *just* closing the dropdown

          const modal = modals.logPayment;
          if (modal && trigger) {
            // --- MODIFIED: Use the 'trigger' variable we found earlier
            if (trigger) {
              //const row = trigger.closest('tr');
              const memberName = row.cells[0].textContent.trim();
              const memberBalance = row.cells[4].textContent.trim().replace('₱', '').replace(',', '');
              const amountInput = modal.querySelector('#log-payment-amount');
              modal.querySelector('#log-member-name').value = memberName;
              modal.querySelector('#log-payment-description').value = '';
              if (parseFloat(memberBalance) > 0) {
                amountInput.value = memberBalance;
              } else {
                amountInput.value = '';
                amountInput.placeholder = '0.00';
              }
              openModal(modal, trigger);
            }
          }
        }

        // --- ADDED: Check if "View Details" was clicked ---
        else if (clickedButton && clickedButton.textContent.trim() === 'View Details') {
          e.preventDefault(); // Stop the click from *just* closing the dropdown

          const modal = modals.viewDetails;
          if (modal && trigger) {

            // --- ADDED: Reset tab state on open ---
            // (This finds the first tab button and programmatically clicks it)
            const firstTab = modal.querySelector('.modal-tab-btn[data-tab="member"]');
            if (firstTab) firstTab.click();
            // --- END ADDED ---

            // --- Populate Modal with Data ---
            // In a real app, this data would come from data-attributes on the row
            //const row = trigger.closest('tr');
            const memberName = row.cells[0].textContent.trim();
            const [firstName, lastName] = memberName.split(' ');

            // Set all VIEW fields
            modal.querySelector('#view-first-name').textContent = firstName || 'N/A';
            modal.querySelector('#view-last-name').textContent = lastName || 'N/A';
            modal.querySelector('#view-email').textContent = 'naruto@konoha.com'; // Placeholder
            modal.querySelector('#view-contact').textContent = '+63 917 123 4567'; // Placeholder
            modal.querySelector('#view-e-name').textContent = 'Kakashi Hatake'; // Placeholder
            modal.querySelector('#view-e-contact').textContent = '+63 917 765 4321'; // Placeholder
            modal.querySelector('#view-medical').textContent = 'None noted'; // Placeholder
            modal.querySelector('#view-goals').textContent = 'To become Hokage!'; // Placeholder

            // Set all EDIT fields
            modal.querySelector('#edit-first-name').value = firstName || '';
            modal.querySelector('#edit-last-name').value = lastName || '';
            modal.querySelector('#edit-email').value = 'naruto@konoha.com'; // Placeholder
            modal.querySelector('#edit-contact').value = '+63 917 123 4567'; // Placeholder
            modal.querySelector('#edit-e-name').value = 'Kakashi Hatake'; // Placeholder
            modal.querySelector('#edit-e-contact').value = '+63 917 765 4321'; // Placeholder
            modal.querySelector('#edit-medical').value = 'None noted'; // Placeholder
            modal.querySelector('#edit-goals').value = 'To become Hokage!'; // Placeholder

            // Set all DISABLED fields
            modal.querySelector('#edit-member-id').value = 'CFH-2025-0001'; // Placeholder
            modal.querySelector('#edit-date-joined').value = '2025-10-25'; // Placeholder
            modal.querySelector('#edit-status').value = row.cells[1].textContent.trim();
            modal.querySelector('#edit-balance').value = row.cells[4].textContent.trim();

            // ALWAYS open in view mode
            modal.classList.remove('is-editing');
            openModal(modal, trigger);
          }
        }
        // --- END ADDED ---

        // --- ADDED: Check if "Freeze" was clicked ---
        else if (clickedButton && clickedButton.textContent.trim() === 'Freeze') {
          e.preventDefault(); // Stop the click from *just* closing the dropdown
          
          const modal = modals.freezeAccount;
          if (modal && trigger) {
            //const row = trigger.closest('tr');
            const memberName = row.cells[0].textContent.trim();
            
            // Pre-fill the read-only member name
            modal.querySelector('#freeze-member-name').value = memberName;
            
            // Store the member name on the confirm button for the handler
            modal.querySelector('#btnConfirmFreeze').dataset.memberName = memberName;
            
            openModal(modal, trigger);
          }
        }
        // --- END ADDED ---

        // --- ADDED: Check if "Check-in/out" was clicked ---
        else if (clickedButton && clickedButton.textContent.trim() === 'Check-in/out') {
          e.preventDefault();
          
          const modal = modals.checkInOut;
          if (modal && trigger) {
            //const row = trigger.closest('tr');
            const memberName = row.cells[0].textContent.trim();
            //const memberStatus = row.cells[1].textContent.trim();
            // --- THIS IS THE FIX ---
            // Read the true status from the data-attribute
            const checkinStatus = row.dataset.checkinStatus;
            
            // Populate the read-only fields
            modal.querySelector('#checkin-member-name').value = memberName;
            
            const statusField = modal.querySelector('#checkin-member-status');
            const actionButton = modal.querySelector('#btnConfirmCheckInOut');
            
            // Store member name for the handler
            actionButton.dataset.memberName = memberName; 

            // --- Dynamic Button Logic ---
            //if (memberStatus.toLowerCase() === 'active') {
            if (checkinStatus === 'checked-in') {
              // Member is CHECKED IN, so show CHECK-OUT button
              statusField.value = 'Checked In';
              actionButton.textContent = 'Check-Out';
              actionButton.classList.remove('modal-btn-approve');
              actionButton.classList.add('modal-btn-reject'); // Red
              actionButton.dataset.action = 'checkout';
            } else {
              // Member is CHECKED OUT, so show CHECK-IN button
              statusField.value = 'Checked Out';
              actionButton.textContent = 'Check-In';
              actionButton.classList.remove('modal-btn-reject');
              actionButton.classList.add('modal-btn-approve'); // Green
              actionButton.dataset.action = 'checkin';
            }

            // ADD THIS NEW LINE:
            actionButton.dataset.memberId = row.dataset.memberId; // <-- Store the ID on the button
            
            openModal(modal, trigger);
          }
        }
        // --- END ADDED ---

        // --- NEW ---
        else if (clickedButton && clickedButton.textContent.trim() === 'Unfreeze') {
          e.preventDefault();

          const modal = modals.unfreezeAccount;
          if (modal && trigger) {
              const memberName = row.cells[0].textContent.trim();

              // Pre-fill the read-only member name
              modal.querySelector('#unfreeze-member-name').value = memberName;

              // Store the member name on the confirm button for the handler
              modal.querySelector('#btnConfirmUnfreeze').dataset.memberName = memberName;

              openModal(modal, trigger);
          }
        }
        // --- END NEW ---

        // --- MODIFIED: This code now runs for *all* clicks inside the dropdown
        openDropdown.classList.remove('is-open');
        const oldTrigger = document.querySelector('.action-menu-btn[aria-expanded="true"]');
        if (oldTrigger) oldTrigger.setAttribute('aria-expanded', 'false');

        if (originalWrapper) {
          originalWrapper.appendChild(openDropdown);
          openDropdown.classList.remove('is-portaled');
          originalWrapper = null;
        }
        return;
      }
      // --- END MODIFIED ---

      // Case 3: Clicked outside everything
      if (openDropdown && !triggerButton) {
        openDropdown.classList.remove('is-open');
        const oldTrigger = document.querySelector('.action-menu-btn[aria-expanded="true"]');
        if (oldTrigger) oldTrigger.setAttribute('aria-expanded', 'false');

        if (originalWrapper) {
          originalWrapper.appendChild(openDropdown);
          openDropdown.classList.remove('is-portaled');
          originalWrapper = null;
        }
      }
    });
  }



  function positionDropdown(dropdown, trigger) {
    const rect = trigger.getBoundingClientRect();
    const dropdownRect = dropdown.getBoundingClientRect();
    const connector = dropdown.querySelector('.dropdown-connector');

    let top = rect.bottom + window.scrollY + 12;
    let left = rect.left + window.scrollX + rect.width / 2 - dropdownRect.width / 2;

    if (left < 8) left = 8;
    const rightEdge = left + dropdownRect.width;
    if (rightEdge > document.documentElement.clientWidth - 8) {
      left = document.documentElement.clientWidth - dropdownRect.width - 8;
    }

    dropdown.style.top = `${top}px`;
    dropdown.style.left = `${left}px`;

    if (connector) {
      connector.style.bottom = 'auto';
      connector.style.top = '-10px';
      connector.style.transform = 'translateX(-50%) rotate(180deg)';
    }
  }

  // --- ADDED: New function to manage modal tabs ---
  function initializeModalTabs(modal) {
    const tabButtons = modal.querySelectorAll('.modal-tab-btn');
    const tabPanes = modal.querySelectorAll('.modal-tab-pane');
    const modalContent = modal.querySelector('.modal-content');

    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const tabId = button.dataset.tab;

        // Update tab buttons
        tabButtons.forEach(btn => {
          btn.classList.remove('is-active');
          btn.setAttribute('aria-selected', 'false');
          btn.setAttribute('tabindex', '-1');
        });
        button.classList.add('is-active');
        button.setAttribute('aria-selected', 'true');
        button.setAttribute('tabindex', '0');

        // Update tab panels
        tabPanes.forEach(pane => {
          pane.classList.remove('is-active');
          pane.setAttribute('aria-hidden', 'true');
        });
        const activePane = modal.querySelector(`#tab-${tabId}`);
        if (activePane) {
          activePane.classList.add('is-active');
          activePane.setAttribute('aria-hidden', 'false');
        }

        // Update parent data-attribute
        if (modalContent) {
          modalContent.dataset.activeTab = tabId;
        }
      });
    });
  }

  // ====================================================================
  // INITIALIZATION
  // ====================================================================

  function init() {
    // Modal references
    const modals = {
      logout: document.getElementById('logout-backdrop'),
      approval: document.getElementById('modalApproval'),
      logPayment: document.getElementById('modalLogPayment'), // <-- ADDED
      viewDetails: document.getElementById('modalViewDetails'), // <-- ADDED
      freezeAccount: document.getElementById('modalFreezeAccount'), // <-- ADDED
      checkInOut: document.getElementById('modalCheckInOut'), // <-- ADDED
      unfreezeAccount: document.getElementById('modalUnfreezeAccount'), //New
      activateMembership: document.getElementById('modalActivateMembership') // <-- NEW
    };

    // Setup member management dropdown
    initializeFilterDropdown();
    handleMemberFilterChange('active');

    // --- Close dropdowns on horizontal scroll ---
    document.querySelectorAll('.table-wrap').forEach(tableWrap => {
      let lastScrollLeft = tableWrap.scrollLeft;
      tableWrap.addEventListener('scroll', function () {
        if (tableWrap.scrollLeft !== lastScrollLeft) {
          const openDropdown = document.querySelector('.action-dropdown.is-portaled.is-open');
          if (openDropdown) {
            openDropdown.classList.remove('is-open');
            const oldTrigger = document.querySelector('.action-menu-btn[aria-expanded="true"]');
            if (oldTrigger) oldTrigger.setAttribute('aria-expanded', 'false');
            if (originalWrapper) {
              originalWrapper.appendChild(openDropdown);
              openDropdown.classList.remove('is-portaled');
              originalWrapper = null;
            }
          }
        }
        lastScrollLeft = tableWrap.scrollLeft;
      });
    });

    // --- Search button ---
    const searchBtn = document.getElementById('member-search-btn');
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        const searchInput = document.getElementById('member-search-input');
        if (searchInput && searchInput.value.trim()) {
          console.log('Searching for:', searchInput.value);
        }
      });
    }

    // --- Logout modal logic ---
    const logoutNavButton = document.querySelector('.side-nav a[href="{% url \'logout\' %}"]');
    if (logoutNavButton) {
      logoutNavButton.addEventListener('click', e => {
        e.preventDefault();
        openModal(modals.logout, e.currentTarget);
      });
    }

    // Close modal logic (for all modals)
    document.querySelectorAll('[data-close]').forEach(el => {
      el.addEventListener('click', e => {
        const parentModal = e.target.closest('.modal');
        closeModal(parentModal);
      });
    });

    document.querySelectorAll('.modal').forEach(m => {
      m.addEventListener('click', e => {
        if (e.target === m) {
          closeModal(m);
        }
      });

      //const cancelBtn = m.querySelector('#logout-cancel');
      //const closeBtn = m.querySelector('#logout-close');
      //if (cancelBtn) cancelBtn.addEventListener('click', () => closeModal(modals.logout));
      //if (closeBtn) closeBtn.addEventListener('click', () => closeModal(modals.logout));
    });

    // --- Approval queue modal logic ---
    const approvalTableBody = document.getElementById('approval-queue-tbody');
    if (approvalTableBody) {
      approvalTableBody.addEventListener('click', e => {
        const triggerButton = e.target.closest('.action-btn');
        if (!triggerButton) return;

        e.preventDefault();
        const modal = modals.approval;
        if (!modal) return;

        const reasonText = modal.querySelector('#approval-reason-text');
        const modalTitle = modal.querySelector('.modal-title--enhanced');
        const row = triggerButton.closest('tr');

        if (row) {
          const memberName = row.cells[1].textContent.trim();
          const requestType = row.cells[0].textContent.trim();
          const reason = triggerButton.dataset.reason || `Placeholder reason from ${memberName}.`;
          const requestId = triggerButton.dataset.requestId || 'temp-id';

          if (reasonText) reasonText.value = reason;
          if (modalTitle)
            modalTitle.innerHTML = `Request Account <span class="modal-title-highlight">${requestType}</span>`;

          modal.querySelector('#btnApprove').dataset.requestId = requestId;
          modal.querySelector('#btnReject').dataset.requestId = requestId;
        }

        openModal(modals.approval, triggerButton);
      });
    }

    const approveBtn = document.getElementById('btnApprove');
    const rejectBtn = document.getElementById('btnReject');

    if (approveBtn) {
      approveBtn.addEventListener('click', e => {
        const requestId = e.currentTarget.dataset.requestId;
        console.log('Placeholder: approveRequest() called for ID:', requestId);
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', e => {
        const requestId = e.currentTarget.dataset.requestId;
        console.log('Placeholder: rejectRequest() called for ID:', requestId);
      });
    }

    // --- ADDED: Log Payment Modal Logic ---
    const confirmPaymentBtn = document.getElementById('btnConfirmPayment');
    if (confirmPaymentBtn) {
      confirmPaymentBtn.addEventListener('click', e => {
        // The [data-close] attribute will close the modal automatically
        const memberName = document.getElementById('log-member-name').value;
        const amount = document.getElementById('log-payment-amount').value;

        console.log(`Placeholder: confirmPayment() called for ${memberName} with amount ${amount}`);
        // Example: sendPayment(memberName, amount);
      });
    }
    // --- END ADDED ---

    // --- ADDED: View/Edit Modal Button Logic ---
    const modalViewDetails = modals.viewDetails;

    if (modalViewDetails) {
      // --- ADDED: Initialize tab switching for this modal ---
      initializeModalTabs(modalViewDetails);
      // --- END ADDED ---
      const btnEditProfile = modalViewDetails.querySelector('#btnEditProfile');
      const btnSaveChanges = modalViewDetails.querySelector('#btnSaveChanges');
      const btnCancelEdit = modalViewDetails.querySelector('#btnCancelEdit');

      // "Edit Profile" button -> Switch to Edit Mode
      if (btnEditProfile) {
        btnEditProfile.addEventListener('click', () => {
          modalViewDetails.classList.add('is-editing');
          // Focus the first input field
          const firstInput = modalViewDetails.querySelector('#edit-first-name');
          if (firstInput) firstInput.focus();
        });
      }

      // "Cancel" (in edit mode) -> Revert to View Mode
      if (btnCancelEdit) {
        btnCancelEdit.addEventListener('click', () => {
          modalViewDetails.classList.remove('is-editing');
          // Optional: Reset form fields to their original values here
          // (The closeModal function already handles a full reset if closed)
        });
      }

      // "Save Changes" -> Placeholder log
      if (btnSaveChanges) {
        btnSaveChanges.addEventListener('click', () => {
          // The [data-close] attribute handles closing
          console.log('Placeholder: Saving member details...');
          // In a real app, you would get form data and send API request
          // On success, the modal closes. On error, you'd show a message.
        });
      }
    }
    // --- END ADDED ---

    // --- ADDED: Freeze Account Modal Logic ---
    const btnConfirmFreeze = document.getElementById('btnConfirmFreeze');

    if (btnConfirmFreeze) {
      btnConfirmFreeze.addEventListener('click', (e) => {
        const memberName = e.currentTarget.dataset.memberName;
        const reason = document.getElementById('freeze-reason').value;

        // TODO: Add form validation here (e.g., check if reason is empty)
        console.log(`Placeholder: confirmFreeze() called for ${memberName}`);
        console.log(`Reason: ${reason}`);

        // Manually close the modal on success
        closeModal(modals.freezeAccount);
      });
    }
    // --- END ADDED ---

    // ==========================================================
    // THIS IS THE CORRECT AND ONLY CHECK-IN/OUT LOGIC
    // ==========================================================

    // --- ADDED: Check-In/Out Modal Logic ---
    const checkInOutModal = modals.checkInOut; // Get modal from our object

    // --- DELETE THIS DUPLICATE LINE ---
    // if (!checkInOutModal) return; // <-- DELETE THIS

    if (checkInOutModal) { // <-- This check is correct
        const confirmButton = checkInOutModal.querySelector('#btnConfirmCheckInOut');

        if (confirmButton) {
            confirmButton.addEventListener('click', () => {
                const memberId = confirmButton.dataset.memberId;
                const action = confirmButton.dataset.action;
                const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

                // Send the data to the server
                fetch('/staff/check-in-out/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        'member_id': memberId,
                        'action': action
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        location.reload();
                    } else {
                        alert(data.message);
                    }
                });
            });
        }
    }
    // ==========================================================

    // --- END ADDED ---

    // --- NEW ---
    const btnConfirmUnfreeze = document.getElementById('btnConfirmUnfreeze');

    if (btnConfirmUnfreeze) {
      btnConfirmUnfreeze.addEventListener('click', (e) => {
        const memberName = e.currentTarget.dataset.memberName;
        const reason = document.getElementById('unfreeze-reason').value;

        // TODO: Add form validation here (e.g., check if reason is empty)
        console.log(`Placeholder: confirmUnfreeze() called for ${memberName}`);
        console.log(`Reason: ${reason}`);

        // Manually close the modal on success
        closeModal(modals.unfreezeAccount);
      });
    }
    // --- END NEW ---

    // --- NEW: Activate Membership Modal Logic ---
    const pendingTableBody = document.getElementById('member-management-tbody-pending');
    if (pendingTableBody) {
      // Use event delegation on the 'Pending' table
      pendingTableBody.addEventListener('click', e => {
        const triggerButton = e.target.closest('.activate-member-btn');
        if (!triggerButton) return; // Didn't click the button

        e.preventDefault();
        const modal = modals.activateMembership;
        if (!modal) return;

        const row = triggerButton.closest('tr');
        const memberName = row.cells[0].textContent.trim();
        const amount = row.cells[2].textContent.trim().replace('₱', '').replace(',', '');
        const memberId = row.dataset.memberId; // Assuming you add data-member-id to the <tr>

        // Pre-fill the modal
        modal.querySelector('#activate-member-name').value = memberName;
        modal.querySelector('#activate-amount').value = amount;

        // Store ID on button for the handler
        const confirmBtn = modal.querySelector('#btnConfirmActivation');
        if (confirmBtn) {
          confirmBtn.dataset.memberId = memberId;
          confirmBtn.dataset.memberName = memberName;
        }

        openModal(modal, triggerButton);
      });
    }

    const btnConfirmActivation = document.getElementById('btnConfirmActivation');
    if (btnConfirmActivation) {
      btnConfirmActivation.addEventListener('click', e => {
        const memberId = e.currentTarget.dataset.memberId;
        const memberName = e.currentTarget.dataset.memberName;

        console.log(`Placeholder: confirmActivation() called for ${memberName} (ID: ${memberId})`);
        // TODO: Add logic to activate member via API

        // Manually close the modal on success
        closeModal(modals.activateMembership);
      });
    }
    // --- END NEW ---


    // Initialize dropdowns
    initializeActionDropdowns(modals);
  }

  // Run init() on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
