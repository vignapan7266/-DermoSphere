(function() {
    // 1. Verify authenticated state immediately
    if (!sessionStorage.getItem('dermoAuthToken')) {
        window.location.replace('logout.html');
        return;
    }

    const INACTIVITY_LIMIT = 120000; // 2 Minutes in milliseconds
    let activityTimeout;
    
    // Inject the Lock Modal DOM dynamically so it doesn't clutter the HTML files
    const modalHTML = `
        <div id="sessionLockOverlay" class="session-lock-overlay">
            <div class="glass-panel lock-modal">
                <div class="lock-icon">🔒</div>
                <h3 style="margin-bottom: 1rem;">Session Paused</h3>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem;">
                    For security purposes, your session has been locked due to inactivity. Please solve the captcha to resume.
                </p>
                <div class="captcha-container" style="justify-content: center;">
                    <canvas id="lockCaptchaCanvas" width="150" height="50"></canvas>
                    <button type="button" class="refresh-captcha" onclick="generateLockCaptcha()" title="Reload Image">⟳</button>
                </div>
                <input type="text" class="input-glass" id="lockCaptchaInput" placeholder="Enter code" autocomplete="off" style="margin-bottom: 1.5rem; text-align: center;">
                
                <div style="display: flex; gap: 1rem;">
                    <button class="btn-cyber" id="unlockBtn" style="flex: 1;">Unlock</button>
                    <button class="btn-cyber" id="terminateBtn" style="flex: 1; background: transparent; border-color: var(--clr-danger); color: var(--clr-danger);">Terminate</button>
                </div>
                <p id="lockErrorMsg" style="color: var(--clr-danger); margin-top: 1rem; font-size: 0.85rem; display: none;"></p>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const overlay = document.getElementById('sessionLockOverlay');
    let currentLockCaptcha = "";

    // Internal Captcha generator specific to the lock screen
    window.generateLockCaptcha = function() {
        const canvas = document.getElementById('lockCaptchaCanvas');
        const ctx = canvas.getContext('2d');
        const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        currentLockCaptcha = "";
        
        ctx.fillStyle = "#f8fafc";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        for (let i = 0; i < 60; i++) {
            ctx.fillStyle = `rgba(${Math.random()*255}, ${Math.random()*255}, ${Math.random()*255}, 0.5)`;
            ctx.beginPath();
            ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, Math.random() * 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        for (let i = 0; i < 4; i++) {
            ctx.strokeStyle = `rgba(${Math.random()*255}, ${Math.random()*255}, ${Math.random()*255}, 0.8)`;
            ctx.lineWidth = Math.random() * 2;
            ctx.beginPath(); ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
            ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height); ctx.stroke();
        }
        
        for (let i = 0; i < 5; i++) {
            const char = chars.charAt(Math.floor(Math.random() * chars.length));
            currentLockCaptcha += char;
            ctx.font = `${22 + Math.random() * 6}px "Courier New", monospace`;
            ctx.fillStyle = "#0b0f19";
            ctx.save();
            ctx.translate(20 + i * 25, 30 + (Math.random() * 6 - 3));
            ctx.rotate((Math.random() * 0.4) - 0.2);
            ctx.fillText(char, 0, 0);
            ctx.restore();
        }
    };

    function lockSession() {
        if (overlay.classList.contains('active')) return; // Already locked
        overlay.classList.add('active');
        generateLockCaptcha();
        document.getElementById('lockCaptchaInput').value = '';
        document.getElementById('lockErrorMsg').style.display = 'none';
    }

    function resetTimer() {
        if (overlay.classList.contains('active')) return; // Don't track background activity if locked
        clearTimeout(activityTimeout);
        sessionStorage.setItem('dermoLastActivity', Date.now().toString());
        activityTimeout = setTimeout(lockSession, INACTIVITY_LIMIT);
    }

    // Attach activity listeners (Debounced implicitly by clearTimeout)
    ['mousemove', 'keydown', 'scroll', 'touchstart', 'click'].forEach(evt => {
        window.addEventListener(evt, resetTimer, { passive: true });
    });

    // Unlock Logic
    document.getElementById('unlockBtn').addEventListener('click', () => {
        const input = document.getElementById('lockCaptchaInput').value.toUpperCase();
        if (input === currentLockCaptcha) {
            overlay.classList.remove('active');
            resetTimer(); // Restart the clock
        } else {
            document.getElementById('lockErrorMsg').textContent = "Incorrect code. Verification failed.";
            document.getElementById('lockErrorMsg').style.display = 'block';
            generateLockCaptcha();
            document.getElementById('lockCaptchaInput').value = '';
        }
    });

    // Terminate Logic
    document.getElementById('terminateBtn').addEventListener('click', () => {
        window.location.replace('logout.html');
    });

    // Start timer on load
    resetTimer();
})();