/**
 * Leaderboard Tab Switching and Table Rendering
 */

// Current active tab (will be set to first leaderboard)
let currentTab = null;

// Sort state (initially null, will be set on first sort)
let sortState = {
    column: null,
    direction: 'desc'
};

/**
 * Get first leaderboard name from embedded data
 */
function getFirstLeaderboardName() {
    const dataElement = document.getElementById('leaderboard-data');
    if (!dataElement) return null;

    const leaderboards = JSON.parse(dataElement.textContent);
    return leaderboards.length > 0 ? leaderboards[0].name : null;
}

/**
 * Resolve the initial leaderboard from the URL hash when possible.
 */
function getInitialLeaderboardName() {
    const hash = window.location.hash.replace('#', '').trim();
    const firstLeaderboard = getFirstLeaderboardName();

    if (!hash) return firstLeaderboard;

    const leaderboardNames = getLeaderboardNames();
    return leaderboardNames.includes(hash) ? hash : firstLeaderboard;
}

/**
 * Get leaderboard names from the embedded payload.
 */
function getLeaderboardNames() {
    const dataElement = document.getElementById('leaderboard-data');
    if (!dataElement) return [];

    const leaderboards = JSON.parse(dataElement.textContent);
    return leaderboards.map(leaderboard => leaderboard.name);
}

/**
 * Initialize leaderboard functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    // Set current tab to first leaderboard
    currentTab = getInitialLeaderboardName();

    initTabs();
    initSorting();
    initUnavailableTabTooltips();

    // Show each leaderboard sorted by resolved score on initial load.
    if (currentTab) {
        switchTab(currentTab, { force: true, syncHash: false });
    }
});

/**
 * Initialize tab switching
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (button.getAttribute('aria-disabled') === 'true') return;

            const tab = button.getAttribute('data-tab');
            switchTab(tab);
        });
    });
}

/**
 * Show a lightweight tooltip for target tabs that are planned but unreleased.
 */
function initUnavailableTabTooltips() {
    const unavailableTabs = document.querySelectorAll('.target-tab-button[aria-disabled="true"][data-tooltip]');
    if (!unavailableTabs.length) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'target-tab-tooltip';
    tooltip.setAttribute('role', 'tooltip');
    document.body.appendChild(tooltip);

    const showTooltip = button => {
        const rect = button.getBoundingClientRect();
        tooltip.textContent = button.getAttribute('data-tooltip');
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.bottom + 10}px`;
        tooltip.classList.add('visible');
    };

    const hideTooltip = () => {
        tooltip.classList.remove('visible');
    };

    unavailableTabs.forEach(button => {
        button.addEventListener('mouseenter', () => showTooltip(button));
        button.addEventListener('focus', () => showTooltip(button));
        button.addEventListener('mouseleave', hideTooltip);
        button.addEventListener('blur', hideTooltip);
    });
}

/**
 * Switch to a different tab
 */
function switchTab(tab, options = {}) {
    const { force = false, syncHash = true } = options;

    if (tab === currentTab && !force) return;

    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
    });

    // Update target-specific one-line descriptions when target tabs exist.
    document.querySelectorAll('[data-mode-panel]').forEach(panel => {
        const activeTargetButton = panel.querySelector(`.target-tab-button[data-tab="${tab}"]`);
        const description = panel.querySelector('[data-target-description-container]');

        if (activeTargetButton && description) {
            description.innerHTML = activeTargetButton.getAttribute('data-target-description') || '';
        }
    });

    // Update benchmark sidebar links
    document.querySelectorAll('.sidebar-benchmark-link').forEach(link => {
        link.classList.toggle('active', link.getAttribute('data-leaderboard') === tab);
    });

    // Update content visibility
    document.querySelectorAll('.leaderboard-content').forEach(content => {
        const contentTab = content.id.replace('-content', '');
        content.style.display = contentTab === tab ? 'block' : 'none';
    });

    currentTab = tab;

    if (syncHash) {
        const nextUrl = `${window.location.pathname}${window.location.search}#${tab}`;
        window.history.replaceState(null, '', nextUrl);
    }

    // Default view is always resolved descending; header clicks still toggle.
    sortTable(tab, 'resolved', { direction: 'desc' });
}

/**
 * Initialize table sorting
 */
function initSorting() {
    const tables = document.querySelectorAll('.leaderboard-table');

    tables.forEach(table => {
        const headers = table.querySelectorAll('th.sortable');

        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                const tableId = table.id;
                const leaderboardName = tableId.replace('-table', '');

                sortTable(leaderboardName, column);
            });
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(leaderboardName, column, options = {}) {
    const table = document.getElementById(`${leaderboardName}-table`);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr.leaderboard-row'));
    const forcedDirection = options.direction;

    // Determine sort direction
    let direction = forcedDirection || 'desc'; // Default to descending for numeric columns
    if (!forcedDirection && sortState.column === column) {
        // Toggle direction if clicking same column
        direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else if (!forcedDirection && (column === 'model' || column === 'org' || column === 'date')) {
        // Text/date columns default to ascending
        direction = 'asc';
    }

    // Update sort state
    sortState = { column, direction };

    // Update header classes
    table.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        if (th.getAttribute('data-sort') === column) {
            th.classList.add('active', direction);
        }
    });

    // Sort rows
    rows.sort((a, b) => {
        let aValue = a.getAttribute(`data-${column}`);
        let bValue = b.getAttribute(`data-${column}`);

        // Convert to numbers if applicable
        if (!isNaN(aValue) && !isNaN(bValue)) {
            aValue = parseFloat(aValue);
            bValue = parseFloat(bValue);
        }

        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));

    // Update rankings
    updateRankings(leaderboardName);
}

/**
 * Update row rankings (visible only)
 */
function updateRankings(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr.leaderboard-row');

    let rank = 1;
    rows.forEach(row => {
        const rankCell = row.querySelector('.rank-col');
        if (!rankCell) return;

        const isScored = row.getAttribute('data-scored') === 'true';

        if (!row.classList.contains('hidden') && isScored) {
            rankCell.textContent = rank++;
        } else {
            rankCell.textContent = '';
        }
    });
}

/**
 * Get visible row count for a leaderboard
 */
function getVisibleRowCount(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    const rows = table.querySelectorAll('tbody tr.leaderboard-row:not(.hidden)');
    return rows.length;
}

/**
 * Export functions for use in other modules
 */
window.leaderboard = {
    updateRankings,
    getVisibleRowCount,
    currentTab: () => currentTab,
    switchTab
};
