(function () {
  'use strict';

  function handleMemberFilterChange() {
    var dropdown = document.getElementById('member-filter-dropdown');
    var searchGroup = document.getElementById('member-search-group');
    
    if (!dropdown || !searchGroup) {
      return;
    }

    var selectedValue = dropdown.value;
    
    // Hide all tbody sections first
    var activeTbody = document.getElementById('member-management-tbody');
    var pendingTbody = document.getElementById('member-management-tbody-pending');
    var frozenTbody = document.getElementById('member-management-tbody-frozen');
    
    if (activeTbody) activeTbody.style.display = 'none';
    if (pendingTbody) pendingTbody.style.display = 'none';
    if (frozenTbody) frozenTbody.style.display = 'none';
    
    // Show the selected tbody
    if (selectedValue === 'active' && activeTbody) {
      activeTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'flex';
    } else if (selectedValue === 'pending' && pendingTbody) {
      pendingTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'none';
      var searchInput = document.getElementById('member-search-input');
      if (searchInput) {
        searchInput.value = '';
      }
    } else if (selectedValue === 'frozen' && frozenTbody) {
      frozenTbody.style.display = 'table-row-group';
      searchGroup.style.display = 'none';
      var searchInput = document.getElementById('member-search-input');
      if (searchInput) {
        searchInput.value = '';
      }
      // Attach popup listeners for frozen accounts
      attachFrozenPopupListeners();
    }
  }
  
  function attachFrozenPopupListeners() {
    var frozenButtons = document.querySelectorAll('.frozen-menu-btn');
    frozenButtons.forEach(function(btn) {
      // Check if button already has a listener by checking for data attribute
      if (btn.dataset.listenerAttached === 'true') {
        return;
      }
      
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        var memberIndex = this.getAttribute('data-member-index');
        var popup = document.getElementById('frozen-popup-' + memberIndex);
        
        // Close all other popups
        var allPopups = document.querySelectorAll('.frozen-menu-popup');
        allPopups.forEach(function(p) {
          if (p !== popup) {
            p.style.display = 'none';
          }
        });
        
        // Toggle current popup
        if (popup) {
          popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
        }
      });
      
      // Mark button as having listener attached
      btn.dataset.listenerAttached = 'true';
    });

    // Close popups when clicking outside (only attach once)
    if (!window.frozenPopupClickListenerAttached) {
      document.addEventListener('click', function(e) {
        if (!e.target.closest('.action-menu-wrapper')) {
          var allPopups = document.querySelectorAll('.frozen-menu-popup');
          allPopups.forEach(function(p) {
            p.style.display = 'none';
          });
        }
      });
      window.frozenPopupClickListenerAttached = true;
    }
  }

  function init() {
    // Set up Approval Queue action buttons
    var approvalButtons = document.querySelectorAll('.approval-table .action-btn');
    approvalButtons.forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        // Placeholder for future popup functionality
        console.log('Approval Queue action clicked');
      });
    });
    
    // Set up Member Management dropdown
    var memberFilter = document.getElementById('member-filter-dropdown');
    if (memberFilter) {
      var searchGroup = document.getElementById('member-search-group');
      if (searchGroup) {
        searchGroup.style.display = 'flex';
      }
      
      // Ensure active tbody is visible by default
      var activeTbody = document.getElementById('member-management-tbody');
      if (activeTbody) {
        activeTbody.style.display = 'table-row-group';
      }
      
      // Hide other tbody sections by default
      var pendingTbody = document.getElementById('member-management-tbody-pending');
      var frozenTbody = document.getElementById('member-management-tbody-frozen');
      if (pendingTbody) pendingTbody.style.display = 'none';
      if (frozenTbody) frozenTbody.style.display = 'none';
      
      memberFilter.addEventListener('change', handleMemberFilterChange);
    }

    var searchBtn = document.getElementById('member-search-btn');
    if (searchBtn) {
      searchBtn.addEventListener('click', function() {
        var searchInput = document.getElementById('member-search-input');
        if (searchInput && searchInput.value.trim()) {
          console.log('Searching for:', searchInput.value);
        }
      });
    }

    var sections = document.querySelectorAll('[data-section]');
    
    sections.forEach(function (section) {
      var shouldFail = section.dataset.section === 'approvals' ? false : false;
      var fallback = section.querySelector('.fallback');
      if (fallback) {
        fallback.style.display = shouldFail ? 'block' : 'none';
      }
    });

    var openBtn = document.getElementById('open-logout');
    var backdrop = document.getElementById('logout-backdrop');
    var cancelBtn = document.getElementById('logout-cancel');
    var closeBtn = document.getElementById('logout-close');

    function openModal() {
      if (backdrop) {
        backdrop.classList.add('is-open');
        backdrop.setAttribute('aria-hidden', 'false');
      }
    }

    function closeModal() {
      if (backdrop) {
        backdrop.classList.remove('is-open');
        backdrop.setAttribute('aria-hidden', 'true');
      }
    }

    if (openBtn) {
      openBtn.addEventListener('click', function (e) {
        e.preventDefault();
        openModal();
      });
    }

    if (cancelBtn) {
      cancelBtn.addEventListener('click', function () {
        closeModal();
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        closeModal();
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) closeModal();
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
