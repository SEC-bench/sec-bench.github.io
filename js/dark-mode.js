// Dark Mode Toggle Functionality

(function() {
    'use strict';

    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';

    // Apply theme on page load immediately (before DOM ready)
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const toggleButton = document.getElementById('dark-mode-toggle');
        const toggleSwitch = document.querySelector('.toggle-switch');
        const sunIcon = document.getElementById('sun-icon');
        const moonIcon = document.getElementById('moon-icon');

        if (!toggleButton || !toggleSwitch) {
            console.error('Dark mode toggle elements not found');
            return;
        }

        // Set initial state based on saved theme
        updateToggleState(savedTheme);

        // Toggle button click handler
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();

            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            console.log('Toggling theme from', currentTheme || 'light', 'to', newTheme);

            // Update theme
            if (newTheme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }

            // Save preference
            localStorage.setItem('theme', newTheme);

            // Update toggle state
            updateToggleState(newTheme);
        });

        function updateToggleState(theme) {
            console.log('Updating toggle state to:', theme);

            if (theme === 'dark') {
                toggleSwitch.classList.add('active');
                if (sunIcon) {
                    sunIcon.style.display = 'none';
                }
                if (moonIcon) {
                    moonIcon.style.display = 'block';
                }
            } else {
                toggleSwitch.classList.remove('active');
                if (sunIcon) {
                    sunIcon.style.display = 'block';
                }
                if (moonIcon) {
                    moonIcon.style.display = 'none';
                }
            }
        }
    });
})();
