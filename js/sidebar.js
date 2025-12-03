/**
 * Sidebar navigation functionality
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    const sidebarSublinks = document.querySelectorAll('.sidebar-sublink');
    const aboutCategory = document.getElementById('about-category');
    const aboutSubmenu = document.getElementById('about-submenu');
    const sections = document.querySelectorAll('.content-section');
    const aboutSubsections = document.querySelectorAll('.about-subsection');

    // Handle collapsible About category
    if (aboutCategory && aboutSubmenu) {
        aboutCategory.addEventListener('click', (e) => {
            e.preventDefault();
            aboutCategory.classList.toggle('collapsed');
            aboutSubmenu.classList.toggle('collapsed');
        });
    }

    // Handle main sidebar links (Leaderboard)
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            const currentPath = window.location.pathname;
            const currentPage = currentPath.split('/').pop() || 'index.html';

            // If we're on a different page, navigate to index.html
            if (currentPage !== 'index.html' && currentPage !== '') {
                // Allow normal navigation to index.html
                return; // Let the browser handle navigation
            }

            // Otherwise, handle as in-page navigation
            e.preventDefault();
            const section = link.getAttribute('data-section');

            // Update active state for main links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Clear active state for sublinks
            sidebarSublinks.forEach(sl => sl.classList.remove('active'));

            // Show the corresponding section
            if (section) {
                showSection(section);
            }
        });
    });

    // Handle About subsection links
    sidebarSublinks.forEach(sublink => {
        // Skip external links - let them work normally
        if (sublink.classList.contains('sidebar-external-link')) {
            return;
        }

        // Check if this is a link to a separate HTML page (like contact.html, citations.html)
        const href = sublink.getAttribute('href');
        const isHtmlPage = href && (href.endsWith('.html') || href.startsWith('http') || href.startsWith('//'));

        // If it's a separate page, let it navigate normally
        if (isHtmlPage) {
            // Update active state when navigating to a page
            sublink.addEventListener('click', () => {
                // Update active state for all links
                sidebarLinks.forEach(l => l.classList.remove('active'));
                sidebarSublinks.forEach(sl => sl.classList.remove('active'));
                sublink.classList.add('active');
            });
            return; // Allow normal navigation
        }

        // Otherwise, handle as in-page navigation
        sublink.addEventListener('click', (e) => {
            e.preventDefault();
            const section = sublink.getAttribute('data-section');
            const subsection = sublink.getAttribute('data-subsection');

            // Update active state for main links
            sidebarLinks.forEach(l => l.classList.remove('active'));

            // Update active state for sublinks
            sidebarSublinks.forEach(sl => sl.classList.remove('active'));
            sublink.classList.add('active');

            // Show About section
            if (section) {
                showSection(section);
            }

            // Show the corresponding subsection
            if (subsection) {
                showAboutSubsection(subsection);
            }
        });
    });

    function showSection(sectionId) {
        sections.forEach(section => {
            if (section.id === `${sectionId}-section`) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        });
    }

    function showAboutSubsection(subsectionName) {
        aboutSubsections.forEach(subsection => {
            if (subsection.id === `about-${subsectionName}`) {
                subsection.style.display = 'block';
            } else {
                subsection.style.display = 'none';
            }
        });
    }

    // Initialize: show leaderboard by default, About submenu expanded by default
    // Check if we're on a separate page (not index.html)
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';

    if (currentPage !== 'index.html' && currentPage !== '') {
        // We're on a separate page, highlight the corresponding link
        sidebarLinks.forEach(l => l.classList.remove('active'));
        sidebarSublinks.forEach(sl => {
            const href = sl.getAttribute('href');
            if (href && (href === currentPage || href.includes(currentPage))) {
                sl.classList.add('active');
            } else {
                sl.classList.remove('active');
            }
        });
    } else {
        // We're on the index page, show leaderboard section
        showSection('leaderboard');
    }
});
