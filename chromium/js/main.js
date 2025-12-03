if (sessionStorage.getItem('authenticated') !== 'true') {
    window.location.href = 'login.html';
} else {
    // Show content after authentication
    document.querySelector('.container').style.display = 'block';
}

const reports = JSON.parse(sessionStorage.getItem('reports_data') || '[]');

function groupByYear(reports) {
    const grouped = {};
    const stats = {};
    
    reports.forEach(report => {
        const year = report.year;
        if (!year) return;
        
        if (!grouped[year]) {
            grouped[year] = [];
            stats[year] = { total: 0, rewarded: 0, totalReward: 0 };
        }
        
        grouped[year].push(report);
        stats[year].total++;
        
        if (report.reward && report.reward !== '-' && report.reward !== '(unknown)') {
            stats[year].rewarded++;
            const rewardMatch = report.reward.match(/\d+/);
            if (rewardMatch) {
                stats[year].totalReward += parseInt(rewardMatch[0]);
            }
        }
    });
    
    return { grouped, stats };
}

function renderYearNav(years) {
    const yearNav = document.getElementById('yearNav');
    const existingButtons = yearNav.querySelectorAll('.year-badge:not([data-year="all"])');
    existingButtons.forEach(btn => btn.remove());
    
    years.forEach(year => {
        const button = document.createElement('button');
        button.className = 'year-badge';
        button.setAttribute('data-year', year);
        button.textContent = year;
        yearNav.appendChild(button);
    });
}

function renderReports(grouped, stats) {
    const content = document.getElementById('content');
    content.innerHTML = '';
    
    const years = Object.keys(grouped).sort((a, b) => b - a);
    
    years.forEach(year => {
        const section = document.createElement('div');
        section.className = 'year-section';
        section.id = `year-${year}`;
        
        const headerRow = document.createElement('div');
        headerRow.className = 'year-header-row';
        headerRow.innerHTML = `
            <h2 class="year-header">${year}</h2>
            <span class="year-total">Total: ${stats[year].total} reports</span>
        `;
        section.appendChild(headerRow);
        
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';
        
        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th class="sortable" data-year="${year}">Reward<span class="sort-icon">⇅</span></th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;
        
        const tbody = table.querySelector('tbody');
        grouped[year].forEach(report => {
            const row = document.createElement('tr');
            row.setAttribute('data-reward', report.reward || '-');
            
            const isUnknownReward = !report.reward || report.reward === '-' || report.reward === '(unknown)';
            
            row.innerHTML = `
                <td class="bug-id">${report.id || ''}</td>
                <td class="bug-title">
                    <a href="${report.link || '#'}" target="_blank">${report.title || 'Unknown'}</a>
                </td>
                <td><span class="category">${report.source || 'Unknown'}</span></td>
                <td class="reward ${isUnknownReward ? 'unknown' : ''}">
                    ${report.reward || '-'}
                </td>
                <td class="date">${report.date || ''}</td>
            `;
            
            tbody.appendChild(row);
        });
        
        tableContainer.appendChild(table);
        section.appendChild(tableContainer);
        content.appendChild(section);
    });
}

const { grouped, stats } = groupByYear(reports);
const years = Object.keys(grouped).sort((a, b) => b - a);

document.getElementById('totalCount').textContent = `Total: ${reports.length} reports`;

renderYearNav(years);
renderReports(grouped, stats);

const searchInput = document.getElementById('searchInput');
let activeYear = 'all';

function filterReports() {
    const searchTerm = searchInput.value.toLowerCase();
    let totalVisibleCount = 0;
    
    document.querySelectorAll('.year-section').forEach(section => {
        const sectionYear = section.id.replace('year-', '');
        
        if (activeYear !== 'all' && sectionYear !== activeYear) {
            section.classList.add('hidden');
            return;
        }
        
        const rows = section.querySelectorAll('tbody tr');
        let visibleInSection = 0;
        
        rows.forEach(row => {
            const id = row.querySelector('.bug-id').textContent.toLowerCase();
            const title = row.querySelector('.bug-title a').textContent.toLowerCase();
            const category = row.querySelector('.category').textContent.toLowerCase();
            
            const matchesSearch = !searchTerm || 
                id.includes(searchTerm) || 
                title.includes(searchTerm) || 
                category.includes(searchTerm);
            
            if (matchesSearch) {
                row.classList.remove('hidden');
                visibleInSection++;
                totalVisibleCount++;
            } else {
                row.classList.add('hidden');
            }
        });
        
        if (visibleInSection === 0) {
            section.classList.add('hidden');
        } else {
            section.classList.remove('hidden');
        }
    });
    
    const existingNoResults = document.querySelector('.no-results');
    if (totalVisibleCount === 0 && !existingNoResults) {
        const noResults = document.createElement('div');
        noResults.className = 'no-results';
        noResults.innerHTML = '🔍 No reports found matching your criteria';
        document.querySelector('.content').appendChild(noResults);
    } else if (totalVisibleCount > 0 && existingNoResults) {
        existingNoResults.remove();
    }
}

searchInput.addEventListener('input', filterReports);

document.querySelectorAll('.year-badge').forEach(badge => {
    badge.addEventListener('click', function() {
        activeYear = this.getAttribute('data-year');
        
        document.querySelectorAll('.year-badge').forEach(b => {
            b.classList.remove('active');
        });
        this.classList.add('active');
        
        filterReports();
    });
});

document.querySelectorAll('.sortable').forEach(header => {
    header.addEventListener('click', function() {
        const year = this.getAttribute('data-year');
        const yearSection = document.getElementById(`year-${year}`);
        const tbody = yearSection.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        const isAsc = this.classList.contains('sorted-asc');
        
        document.querySelectorAll('.sortable').forEach(h => {
            h.classList.remove('sorted-asc', 'sorted-desc');
        });
        
        rows.sort((a, b) => {
            const rewardA = a.querySelector('.reward').textContent.trim();
            const rewardB = b.querySelector('.reward').textContent.trim();
            
            const getRewardValue = (reward) => {
                if (reward === '-' || reward === '(unknown)') return -1;
                const match = reward.match(/\d+/);
                return match ? parseInt(match[0]) : -1;
            };
            
            const valueA = getRewardValue(rewardA);
            const valueB = getRewardValue(rewardB);
            
            if (isAsc) {
                return valueB - valueA;
            } else {
                return valueA - valueB;
            }
        });
        
        if (isAsc) {
            this.classList.add('sorted-desc');
        } else {
            this.classList.add('sorted-asc');
        }
        
        rows.forEach(row => tbody.appendChild(row));
    });
});

function showNotification(message, isError = false) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification' + (isError ? ' error' : '');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'fadeInUp 0.6s ease-out';
        }
    });
}, observerOptions);

document.querySelectorAll('.year-section').forEach(section => {
    observer.observe(section);
});

