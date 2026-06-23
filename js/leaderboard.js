/**
 * Leaderboard tabs, score-mode switching, sorting, and detail-row navigation.
 */

let currentTab = null;
let currentScoreMode = 'headline';
let sortState = {
    column: null,
    direction: 'desc'
};

function getLeaderboards() {
    const dataElement = document.getElementById('leaderboard-data');
    if (!dataElement) return [];
    try {
        return JSON.parse(dataElement.textContent);
    } catch {
        return [];
    }
}

function getFirstLeaderboardName() {
    const leaderboards = getLeaderboards();
    return leaderboards.length > 0 ? leaderboards[0].name : null;
}

function getLeaderboardNames() {
    return getLeaderboards().map(leaderboard => leaderboard.name);
}

function getLeaderboardNameFromPath() {
    const segments = window.location.pathname.split('/').filter(Boolean);
    if (!segments.length) return null;

    const names = getLeaderboardNames();
    return segments.find(candidate => names.includes(candidate)) || null;
}

function getTargetUrlForTab(tab) {
    const buttons = document.querySelectorAll('.target-tab-button[data-target-url]');
    for (const button of buttons) {
        if (button.getAttribute('data-tab') === tab) {
            return button.getAttribute('data-target-url');
        }
    }
    return null;
}

function getInitialLeaderboardName() {
    const pathLeaderboard = getLeaderboardNameFromPath();
    if (pathLeaderboard) return pathLeaderboard;

    const hash = window.location.hash.replace('#', '').trim();
    const names = getLeaderboardNames();
    return names.includes(hash) ? hash : getFirstLeaderboardName();
}

function getScopeForTab(tab) {
    const button = document.querySelector(`.target-tab-button[data-tab="${tab}"]`);
    return button?.closest('[data-mode-panel]') || document;
}

function updateVersionControls(tab) {
    document.querySelectorAll('[data-version-link]').forEach(link => {
        const targetUrl = link.getAttribute(`data-version-url-${tab}`);
        const overallUrl = link.getAttribute('data-version-url-overall');
        const nextUrl = targetUrl || overallUrl;

        if (nextUrl) {
            link.setAttribute('href', nextUrl);
        }

        const fallback = !targetUrl && tab !== 'overall';
        link.classList.toggle('version-tab-fallback', fallback);

        const baseTitle = link.getAttribute('data-version-title') || '';
        if (fallback) {
            link.setAttribute('title', `${baseTitle} - opens Overall; selected target is not in this snapshot`);
        } else {
            link.setAttribute('title', baseTitle);
        }
    });

    document.querySelectorAll('[data-version-select]').forEach(select => {
        let selectedTitle = '';
        let selectedFallback = false;

        Array.from(select.options).forEach(option => {
            const targetUrl = option.getAttribute(`data-version-url-${tab}`);
            const overallUrl = option.getAttribute('data-version-url-overall');
            const nextUrl = targetUrl || overallUrl;

            if (nextUrl) {
                option.value = nextUrl;
            }

            const fallback = !targetUrl && tab !== 'overall';
            option.dataset.versionFallback = String(fallback);

            if (option.selected) {
                selectedTitle = option.getAttribute('data-version-title') || '';
                selectedFallback = fallback;
            }
        });

        select.classList.toggle('version-select-fallback', selectedFallback);
        select.setAttribute(
            'title',
            selectedFallback
                ? `${selectedTitle} - opens Overall; selected target is not in this snapshot`
                : selectedTitle
        );
    });
}

document.addEventListener('DOMContentLoaded', () => {
    currentTab = getInitialLeaderboardName();

    initTabs();
    initScoreModes();
    initVersionSelects();
    initSorting();
    initRowNavigation();

    if (currentTab) {
        switchTab(currentTab, { force: true, syncHash: false });
    }
    applyScoreMode(currentScoreMode);
});

function initTabs() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            if (button.getAttribute('aria-disabled') === 'true') return;
            switchTab(button.getAttribute('data-tab'));
        });
    });
}

function initScoreModes() {
    document.querySelectorAll('[data-score-mode]').forEach(button => {
        button.addEventListener('click', () => {
            applyScoreMode(button.getAttribute('data-score-mode'));
        });
    });
}

function initVersionSelects() {
    document.querySelectorAll('[data-version-select]').forEach(select => {
        select.addEventListener('change', () => {
            if (select.value) {
                window.location.href = select.value;
            }
        });
    });
}

function initRowNavigation() {
    document.querySelectorAll('.leaderboard-row[data-details-url]').forEach(row => {
        const openDetails = event => {
            if (event.target.closest('a, button')) return;
            window.location.href = row.getAttribute('data-details-url');
        };

        row.addEventListener('click', openDetails);
        row.addEventListener('keydown', event => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            window.location.href = row.getAttribute('data-details-url');
        });
    });
}

function switchTab(tab, options = {}) {
    const { force = false, syncHash = true } = options;
    if (tab === currentTab && !force) return;
    const scope = getScopeForTab(tab);

    scope.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.getAttribute('data-tab') === tab);
    });

    scope.querySelectorAll('[data-target-description-container]').forEach(description => {
        const activeButton = scope.querySelector(`.target-tab-button[data-tab="${tab}"]`);
        if (activeButton) {
            description.innerHTML = activeButton.getAttribute('data-target-description') || '';
        }
    });

    scope.querySelectorAll('.leaderboard-content').forEach(content => {
        const contentTab = content.id.replace('-content', '');
        content.style.display = contentTab === tab ? 'block' : 'none';
    });

    scope.querySelectorAll('[data-info-panel]').forEach(panel => {
        panel.style.display = panel.getAttribute('data-info-panel') === tab ? 'grid' : 'none';
    });

    currentTab = tab;
    updateVersionControls(tab);

    if (syncHash) {
        const targetUrl = getTargetUrlForTab(tab);
        const nextUrl = targetUrl || `${window.location.pathname}${window.location.search}#${tab}`;
        window.history.replaceState(null, '', nextUrl);
    }

    sortTable(tab, 'resolved', { direction: 'desc' });
}

function applyScoreMode(mode) {
    currentScoreMode = mode || 'headline';

    document.querySelectorAll('[data-score-mode]').forEach(button => {
        const active = button.getAttribute('data-score-mode') === currentScoreMode;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
    });

    document.querySelectorAll('.leaderboard-row').forEach(row => {
        if (!row.hasAttribute(`data-${currentScoreMode}-score`)) {
            return;
        }

        const score = Number.parseFloat(row.getAttribute(`data-${currentScoreMode}-score`) || '0');
        const rank = row.getAttribute(`data-${currentScoreMode}-rank`) || '';
        const scoreLabel = row.getAttribute(`data-${currentScoreMode}-score-label`) || '';
        const count = row.getAttribute(`data-${currentScoreMode}-count`) || '';

        row.setAttribute('data-resolved', String(score));
        row.setAttribute('data-rank', rank);

        row.querySelector('[data-score-value]')?.replaceChildren(document.createTextNode(`${score}%`));
        row.querySelector('[data-count-value]')?.replaceChildren(document.createTextNode(count));
        row.querySelector('[data-rank-value]')?.replaceChildren(document.createTextNode(rank));

        const fill = row.querySelector('.score-bar-fill');
        if (fill) {
            fill.style.width = `${Math.max(0, Math.min(100, score))}%`;
        }

        row.querySelectorAll('.score-segment').forEach(segment => {
            const width = segment.getAttribute(`data-${currentScoreMode}-width`) || '0';
            const title = segment.getAttribute(`data-${currentScoreMode}-title`);
            segment.style.width = `${width}%`;
            if (title) {
                segment.setAttribute('title', title);
            }
        });

        const scoreCell = row.querySelector('.score-cell');
        if (scoreCell) {
            scoreCell.setAttribute('title', scoreLabel);
        }
    });

    if (currentTab) {
        sortTable(currentTab, 'resolved', { direction: 'desc' });
    }
}

function initSorting() {
    document.querySelectorAll('.leaderboard-table').forEach(table => {
        table.querySelectorAll('th.sortable').forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                const leaderboardName = table.id.replace('-table', '');
                sortTable(leaderboardName, column);
            });
        });
    });
}

function defaultDirection(column) {
    if (column === 'model' || column === 'org' || column === 'date') return 'asc';
    if (column === 'rank') return 'asc';
    return 'desc';
}

function sortTable(leaderboardName, column, options = {}) {
    const table = document.getElementById(`${leaderboardName}-table`);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr.leaderboard-row'));
    const forcedDirection = options.direction;

    let direction = forcedDirection || defaultDirection(column);
    if (!forcedDirection && sortState.column === column) {
        direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    }
    sortState = { column, direction };

    table.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        if (th.getAttribute('data-sort') === column) {
            th.classList.add('active', direction);
        }
    });

    rows.sort((a, b) => {
        let aValue = a.getAttribute(`data-${column}`) || '';
        let bValue = b.getAttribute(`data-${column}`) || '';

        const aNumber = Number.parseFloat(aValue);
        const bNumber = Number.parseFloat(bValue);
        if (!Number.isNaN(aNumber) && !Number.isNaN(bNumber)) {
            aValue = aNumber;
            bValue = bNumber;
        } else {
            aValue = aValue.toLowerCase();
            bValue = bValue.toLowerCase();
        }

        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
    updateRankings(leaderboardName);
}

function updateRankings(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr.leaderboard-row');

    rows.forEach(row => {
        const rankBadge = row.querySelector('[data-rank-value]');
        if (!rankBadge) return;

        if (!row.classList.contains('hidden') && row.getAttribute('data-scored') === 'true') {
            const rank = row.getAttribute(`data-${currentScoreMode}-rank`) || row.getAttribute('data-rank') || '';
            rankBadge.textContent = rank;
            rankBadge.classList.toggle('rank-1', rank === '1');
        } else {
            rankBadge.textContent = '';
            rankBadge.classList.remove('rank-1');
        }
    });
}

function getVisibleRowCount(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    if (!table) return 0;
    return table.querySelectorAll('tbody tr.leaderboard-row:not(.hidden)').length;
}

window.leaderboard = {
    updateRankings,
    getVisibleRowCount,
    currentTab: () => currentTab,
    currentScoreMode: () => currentScoreMode,
    switchTab,
    applyScoreMode
};
