/**
 * Sidebar navigation functionality
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    const sidebarSublinks = document.querySelectorAll('.sidebar-sublink');
    const benchmarkLinks = document.querySelectorAll('.sidebar-benchmark-link');
    const sections = document.querySelectorAll('.content-section');
    const proToggle = document.getElementById('pro-toggle');
    const modeButtons = document.querySelectorAll('[data-mode-switch]');
    const modePanels = document.querySelectorAll('[data-mode-panel]');
    const hasLeaderboardPanels = modePanels.length > 0;

    function isExternalNavHref(href) {
        return /^https?:\/\//.test(href || '') || /^\/\//.test(href || '');
    }

    function updateModeNavLinks(mode) {
        document.querySelectorAll('[data-mode-nav-link]').forEach(link => {
            const nextHref = mode === 'classic' ? link.dataset.classicHref : link.dataset.proHref;

            if (!nextHref) {
                link.removeAttribute('href');
                link.setAttribute('aria-disabled', 'true');
                link.removeAttribute('target');
                link.removeAttribute('rel');
                return;
            }

            link.setAttribute('href', nextHref);
            link.removeAttribute('aria-disabled');

            if (isExternalNavHref(nextHref)) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            } else {
                link.removeAttribute('target');
                link.removeAttribute('rel');
            }
        });
    }

    function requestedModeFromLocation() {
        const params = new URLSearchParams(window.location.search);
        const requested = (params.get('mode') || params.get('view') || '').toLowerCase();
        const hash = window.location.hash.replace('#', '').toLowerCase();
        const classicAliases = new Set(['classic', 'legacy', 'secbench', 'sec-bench']);

        if (classicAliases.has(requested) || classicAliases.has(hash)) {
            return 'classic';
        }

        if (requested === 'pro' || hash === 'pro') {
            return 'pro';
        }

        return 'pro';
    }

    function setLeaderboardMode(mode) {
        const isPro = mode === 'pro';

        document.body.setAttribute('data-leaderboard-mode', mode);
        updateModeNavLinks(mode);

        modeButtons.forEach(button => {
            const active = button.getAttribute('data-mode-switch') === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', String(active));
            button.setAttribute('aria-pressed', String(active));
        });

        if (proToggle) {
            proToggle.classList.toggle('active', isPro);
            proToggle.setAttribute('aria-pressed', String(isPro));
            proToggle.setAttribute('data-state', isPro ? 'on' : 'off');
            proToggle.setAttribute('title', isPro ? 'PRO mode on' : 'PRO mode off');
        }

        modePanels.forEach(panel => {
            const isActive = panel.getAttribute('data-mode-panel') === mode;
            panel.hidden = !isActive;
            panel.classList.toggle('mode-panel-active', isActive);

            if (isActive && window.leaderboard) {
                const defaultLeaderboard = panel.getAttribute('data-default-leaderboard');
                if (defaultLeaderboard) {
                    window.leaderboard.switchTab(defaultLeaderboard, { force: true, syncHash: false });
                }
            }
        });
    }

    function showSection(sectionId) {
        sections.forEach(section => {
            const isLeaderboardSection = sectionId === 'leaderboard' && section.classList.contains('leaderboard-section');
            section.style.display = section.id === `${sectionId}-section` || isLeaderboardSection ? 'block' : 'none';
        });
    }

    function activateMainLeaderboardLink() {
        sidebarLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('data-section') === 'leaderboard');
        });

        sidebarSublinks.forEach(link => {
            if (!link.classList.contains('sidebar-benchmark-link')) {
                link.classList.remove('active');
            }
        });
    }

    function activateBenchmarkLink(tabName) {
        benchmarkLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('data-leaderboard') === tabName);
        });
    }

    sidebarLinks.forEach(link => {
        link.addEventListener('click', event => {
            if (!hasLeaderboardPanels) {
                return;
            }

            const currentPage = window.location.pathname.split('/').pop() || 'index.html';

            if (currentPage !== 'index.html' && currentPage !== '') {
                return;
            }

            event.preventDefault();
            activateMainLeaderboardLink();
            showSection('leaderboard');

            if (window.leaderboard) {
                const firstLeaderboard = window.leaderboard.currentTab();
                if (firstLeaderboard) {
                    activateBenchmarkLink(firstLeaderboard);
                }
            }
        });
    });

    benchmarkLinks.forEach(link => {
        link.addEventListener('click', event => {
            if (!hasLeaderboardPanels) {
                return;
            }

            const currentPage = window.location.pathname.split('/').pop() || 'index.html';
            const tabName = link.getAttribute('data-leaderboard');

            if (currentPage !== 'index.html' && currentPage !== '') {
                return;
            }

            event.preventDefault();
            activateMainLeaderboardLink();
            activateBenchmarkLink(tabName);
            showSection('leaderboard');

            if (window.leaderboard) {
                window.leaderboard.switchTab(tabName);
            }
        });
    });

    sidebarSublinks.forEach(sublink => {
        if (sublink.classList.contains('sidebar-external-link')) {
            return;
        }

        if (sublink.classList.contains('sidebar-benchmark-link')) {
            return;
        }

        const href = sublink.getAttribute('href');
        const isHtmlPage = href && (href.endsWith('.html') || href.startsWith('http') || href.startsWith('//'));

        if (isHtmlPage) {
            sublink.addEventListener('click', () => {
                sidebarLinks.forEach(link => link.classList.remove('active'));
                sidebarSublinks.forEach(link => {
                    if (!link.classList.contains('sidebar-benchmark-link')) {
                        link.classList.remove('active');
                    }
                });
                sublink.classList.add('active');
            });
        }
    });

    if (proToggle) {
        proToggle.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();

            const currentMode = document.body.getAttribute('data-leaderboard-mode') || 'pro';
            setLeaderboardMode(currentMode === 'pro' ? 'classic' : 'pro');
        });
    }

    modeButtons.forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();
            const mode = button.getAttribute('data-mode-switch') || 'pro';
            setLeaderboardMode(mode);
        });
    });

    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    const initialMode = requestedModeFromLocation();

    if (!hasLeaderboardPanels) {
        setLeaderboardMode(initialMode);
        activateMainLeaderboardLink();
        return;
    }

    if (currentPage !== 'index.html' && currentPage !== '') {
        setLeaderboardMode(initialMode);
        sidebarLinks.forEach(link => link.classList.remove('active'));
        benchmarkLinks.forEach(link => link.classList.remove('active'));
        sidebarSublinks.forEach(link => {
            if (link.classList.contains('sidebar-benchmark-link')) {
                return;
            }

            const href = link.getAttribute('href');
            if (href && (href === currentPage || href.includes(currentPage))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        return;
    }

    showSection('leaderboard');
    activateMainLeaderboardLink();
    setLeaderboardMode(initialMode);

    if (window.leaderboard) {
        activateBenchmarkLink(window.leaderboard.currentTab());
    }
});
