
const AUTH_API_URL = '/api/v1/auth';

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const userInput = document.getElementById('captchaInput').value;
        const errorMsg = document.getElementById('errorMsg');
        
        // 1. Core verification
        if (!validateCaptcha(userInput)) {
            errorMsg.textContent = "Security verification failed. Please try again.";
            errorMsg.style.display = 'block';
            generateCaptcha(); // Force new challenge
            document.getElementById('captchaInput').value = '';
            return;
        }

        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const targetRole = document.getElementById('loginRole').value;

        // 2. Generate and store JWT / Basic Auth session token
        const basicAuthToken = btoa(`${username}:${password}`);
        sessionStorage.setItem('dermoAuthToken', basicAuthToken);
        sessionStorage.setItem('dermoUserRole', targetRole);
        sessionStorage.setItem('dermoUsername', username);
        
        // Set timestamp for the Session Guard (Inactivity Tracker)
        sessionStorage.setItem('dermoLastActivity', Date.now().toString());

        // 3. RBAC (Role-Based Access Control) Routing Logic
        if (targetRole === 'PATIENT') {
            window.location.replace('patient.html');
        } else if (targetRole === 'DOCTOR') {
            window.location.replace('doctor.html');
        }
    });
}