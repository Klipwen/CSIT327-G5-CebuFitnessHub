(function () {
  'use strict';

  function handleMemberFilterChange() {
    var dropdown = document.getElementById('member-filter-dropdown');
    var searchGroup = document.getElementById('member-search-group');
    
    if (!dropdown || !searchGroup) {
      return;
    }

    var selectedValue = dropdown.value;
    
    // Show search field only when Active Members is selected
    if (selectedValue === 'active') {
      searchGroup.style.display = 'flex';
    } else {
      searchGroup.style.display = 'none';
      var searchInput = document.getElementById('member-search-input');
      if (searchInput) {
        searchInput.value = '';
      }
    }
  }

  function init() {
    var memberFilter = document.getElementById('member-filter-dropdown');
    if (memberFilter) {
      var searchGroup = document.getElementById('member-search-group');
      if (searchGroup) {
        searchGroup.style.display = 'flex';
      }
      
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
