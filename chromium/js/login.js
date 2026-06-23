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

function showAlert(message, type = 'error') {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert alert-${type}`;
    alert.classList.remove('hidden');
}

function hideAlert() {
    const alert = document.getElementById('alert');
    alert.classList.add('hidden');
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const password = document.getElementById('password').value;
    const submitBtn = this.querySelector('.submit-btn');
    
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Decrypting...';
    hideAlert();
    
    try {
        const response = await fetch('../data/chromium/dataset.binj');
        if (!response.ok) {
            throw new Error(`Failed to load data: HTTP ${response.status}`);
        }
        const encryptedData = await response.text();
        
        const decryptedJSON = await decryptData(encryptedData, password);
        
        const data = JSON.parse(decryptedJSON);
        
        sessionStorage.setItem('reports_data', JSON.stringify(data));
        sessionStorage.setItem('decryption_key', password);
        sessionStorage.setItem('authenticated', 'true');
        
        showAlert('✅ Successfully decrypted!', 'success');
        
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 500);
        
    } catch (error) {
        console.error('Error:', error);
        showAlert('❌ Decryption failed: Invalid key or corrupted data');
        
        submitBtn.disabled = false;
        submitBtn.textContent = '🔓 Login';
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
    }
});

// Redirect to index.html if already authenticated
if (sessionStorage.getItem('authenticated') === 'true') {
    window.location.replace('index.html');
}

// Reset form when returning via back button
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        // Restored from bfcache
        const form = document.getElementById('loginForm');
        const alert = document.getElementById('alert');
        const submitBtn = form.querySelector('.submit-btn');
        
        form.reset();
        alert.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = '🔓 Login';
        document.getElementById('password').focus();
    }
});

document.getElementById('password').focus();

