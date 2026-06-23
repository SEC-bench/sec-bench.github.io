/**
 * Citation copy and format switching functionality
 */

function initCitationCopy() {
    const copyBtns = document.querySelectorAll('.citation-container .copy-btn');

    copyBtns.forEach(btn => {
        const citationText = btn.closest('.citation-container').querySelector('pre');

        if (btn && citationText) {
            btn.addEventListener('click', function () {
                const textToCopy = citationText.textContent.trim();

                // Use modern clipboard API if available
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(textToCopy).then(() => {
                        showCopySuccess(btn);
                    }).catch(() => {
                        fallbackCopy(textToCopy, btn);
                    });
                } else {
                    fallbackCopy(textToCopy, btn);
                }
            });
        }
    });
}

function fallbackCopy(text, btn) {
    const tempElement = document.createElement('textarea');
    tempElement.value = text;
    tempElement.setAttribute('readonly', '');
    tempElement.style.position = 'absolute';
    tempElement.style.left = '-9999px';
    document.body.appendChild(tempElement);

    tempElement.select();
    document.execCommand('copy');
    document.body.removeChild(tempElement);

    showCopySuccess(btn);
}

function showCopySuccess(btn) {
    const status = btn.querySelector('.copy-status');

    btn.classList.add('copy-success');
    btn.setAttribute('aria-label', 'Citation copied');
    btn.setAttribute('title', 'Citation copied');
    if (status) {
        status.textContent = 'Citation copied';
    }

    setTimeout(function () {
        btn.classList.remove('copy-success');
        btn.setAttribute('aria-label', 'Copy citation');
        btn.setAttribute('title', 'Copy citation');
        if (status) {
            status.textContent = 'Copy citation';
        }
    }, 2000);
}

function initCitationFormatSwitcher() {
    const formatButtons = document.querySelectorAll('.citation-format-btn');

    formatButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const format = this.getAttribute('data-format');
            const target = this.getAttribute('data-target');
            showCitationFormat(target, format, this);
        });
    });
}

function showCitationFormat(target, format, selectedButton) {
    if (!target || !format) {
        return;
    }

    if (selectedButton) {
        const siblings = selectedButton.parentElement.querySelectorAll('.citation-format-btn');
        siblings.forEach(sib => sib.classList.remove('active'));
        selectedButton.classList.add('active');
    }

    const containers = Array.from(document.querySelectorAll('.citation-container')).filter(
        el => el.getAttribute('data-citation-target') === target
    );

    containers.forEach(el => {
        const isSelected = el.getAttribute('data-format') === format;
        el.classList.toggle('display-none', !isSelected);
        el.classList.toggle('display-block', isSelected);
    });
}

function initCitationTabs() {
    const tabButtons = document.querySelectorAll('.citation-tab-btn');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const tabId = this.getAttribute('data-citation-tab');

            tabButtons.forEach(tab => {
                const isSelected = tab === this;
                tab.classList.toggle('active', isSelected);
                tab.setAttribute('aria-selected', String(isSelected));
            });

            document.querySelectorAll('.citation-tab-panel').forEach(panel => {
                const isSelected = panel.getAttribute('data-citation-panel') === tabId;
                panel.classList.toggle('display-none', !isSelected);
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initCitationCopy();
    initCitationTabs();
    initCitationFormatSwitcher();
});
