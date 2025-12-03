if (sessionStorage.getItem('authenticated') !== 'true') {
    window.location.href = 'login.html';
}

const urlParams = new URLSearchParams(window.location.search);
const reportId = urlParams.get('id');

if (!reportId) {
    window.location.href = 'index.html';
}

async function deriveKey(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return new Uint8Array(hashBuffer);
}

async function decryptData(encryptedBase64, password) {
    try {
        const { chacha20poly1305 } = await import('https://esm.sh/@noble/ciphers@0.5.3/chacha');
        
        const encryptedData = Uint8Array.from(atob(encryptedBase64), c => c.charCodeAt(0));
        
        const nonce = encryptedData.slice(0, 12);
        const ciphertext = encryptedData.slice(12);
        
        const keyBytes = await deriveKey(password);
        
        const aead = chacha20poly1305(keyBytes, nonce);
        const decrypted = aead.decrypt(ciphertext);
        
        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
        
    } catch (error) {
        throw new Error('Decryption failed: ' + error.message);
    }
}

async function loadMarkdown() {
    const password = sessionStorage.getItem('decryption_key');
    if (!password) {
        window.location.href = 'login.html';
        return null;
    }
    
    try {
        const response = await fetch('../data/chromium/dataset.binmd');
        if (!response.ok) {
            throw new Error(`Failed to load markdown: HTTP ${response.status}`);
        }
        const encryptedData = await response.text();
        const decryptedJSON = await decryptData(encryptedData, password);
        return JSON.parse(decryptedJSON);
    } catch (error) {
        console.error('Error loading markdown:', error);
        return null;
    }
}

async function loadAttachments() {
    const password = sessionStorage.getItem('decryption_key');
    if (!password) {
        return null;
    }
    
    try {
        const response = await fetch('../data/chromium/dataset.binat');
        if (!response.ok) {
            throw new Error(`Failed to load attachments: HTTP ${response.status}`);
        }
        const encryptedData = await response.text();
        const decryptedJSON = await decryptData(encryptedData, password);
        return JSON.parse(decryptedJSON);
    } catch (error) {
        console.error('Error loading attachments:', error);
        return null;
    }
}

async function renderMarkdown(markdown) {
    const { marked } = await import('https://esm.sh/marked@11.0.0');
    
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: true,
        mangle: false
    });
    
    return marked.parse(markdown);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function getMimeTypeCategory(mimeType) {
    if (mimeType.startsWith('text/')) return 'text';
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.includes('javascript')) return 'code';
    if (mimeType.includes('python')) return 'code';
    if (mimeType.includes('html')) return 'code';
    return 'binary';
}

function renderAttachments(attachments) {
    const attachmentsSection = document.getElementById('attachmentsSection');
    const attachmentsList = document.getElementById('attachmentsList');
    
    if (!attachments || attachments.length === 0) {
        attachmentsSection.style.display = 'none';
        return;
    }
    
    attachmentsSection.style.display = 'block';
    attachmentsList.innerHTML = '';
    
    attachments.forEach(attachment => {
        const item = document.createElement('div');
        item.className = 'attachment-item';
        
        const category = getMimeTypeCategory(attachment.mime_type);
        const icon = category === 'image' ? '🖼️' : 
                    category === 'code' ? '📄' : 
                    category === 'text' ? '📝' : '📎';
        
        item.innerHTML = `
            <div class="attachment-name">${icon} ${attachment.name}</div>
            <div class="attachment-info">${formatFileSize(attachment.size)} • ${attachment.mime_type}</div>
            <div class="attachment-actions">
                <button class="view-btn" data-name="${attachment.name}">👁️ View</button>
                <button class="download-btn" data-name="${attachment.name}">⬇️ Download</button>
            </div>
        `;
        
        attachmentsList.appendChild(item);
    });
    
    attachmentsList.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const name = btn.dataset.name;
            const attachment = attachments.find(a => a.name === name);
            if (attachment) {
                showAttachment(attachment);
            }
        });
    });
    
    attachmentsList.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const name = btn.dataset.name;
            const attachment = attachments.find(a => a.name === name);
            if (attachment) {
                downloadAttachment(attachment);
            }
        });
    });
}

function showAttachment(attachment) {
    const modal = document.getElementById('attachmentModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = attachment.name;
    modalBody.innerHTML = '';
    
    const category = getMimeTypeCategory(attachment.mime_type);
    const binaryData = atob(attachment.content);
    
    if (category === 'image') {
        const img = document.createElement('img');
        img.src = `data:${attachment.mime_type};base64,${attachment.content}`;
        img.alt = attachment.name;
        modalBody.appendChild(img);
    } else if (category === 'text' || category === 'code') {
        const pre = document.createElement('pre');
        pre.textContent = binaryData;
        modalBody.appendChild(pre);
    } else {
        modalBody.innerHTML = `
            <p>This file type cannot be previewed.</p>
            <p>File: <strong>${attachment.name}</strong></p>
            <p>Type: ${attachment.mime_type}</p>
            <p>Size: ${formatFileSize(attachment.size)}</p>
            <button class="download-btn" style="margin-top: 20px;">⬇️ Download</button>
        `;
        modalBody.querySelector('.download-btn').addEventListener('click', () => {
            downloadAttachment(attachment);
        });
    }
    
    modal.classList.add('show');
}

function downloadAttachment(attachment) {
    const binaryString = atob(attachment.content);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    const blob = new Blob([bytes], { type: attachment.mime_type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = attachment.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

document.getElementById('modalClose').addEventListener('click', () => {
    document.getElementById('attachmentModal').classList.remove('show');
});

document.getElementById('attachmentModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
        e.currentTarget.classList.remove('show');
    }
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    sessionStorage.clear();
    window.location.href = 'login.html';
});

async function init() {
    const reports = JSON.parse(sessionStorage.getItem('reports_data') || '[]');
    const report = reports.find(r => r.id === reportId);
    
    if (!report) {
        document.getElementById('markdownContent').innerHTML = '<p>Report not found.</p>';
        return;
    }
    
    document.getElementById('reportTitle').textContent = report.title;
    document.getElementById('reportDate').textContent = `📅 ${report.date}`;
    document.getElementById('reportCategory').textContent = `📁 ${report.source}`;
    
    if (report.reward) {
        document.getElementById('reportReward').textContent = `💰 $${report.reward}`;
        document.getElementById('reportReward').style.display = 'inline-block';
    } else {
        document.getElementById('reportReward').style.display = 'none';
    }
    
    document.getElementById('reportLink').href = report.link;
    
    const markdownData = await loadMarkdown();
    if (markdownData && markdownData[reportId]) {
        const html = await renderMarkdown(markdownData[reportId]);
        document.getElementById('markdownContent').innerHTML = html;
    } else {
        document.getElementById('markdownContent').innerHTML = '<p>Report content not available.</p>';
    }
    
    const attachmentsData = await loadAttachments();
    if (attachmentsData && attachmentsData[reportId]) {
        renderAttachments(attachmentsData[reportId]);
    }
}

init();

