const AUTH_API_URL = 'http://localhost:8081/api/v1/auth';

// Utility to switch between Login and Register DOM cards
function toggleAuthView(targetCardId) {
    document.getElementById('loginCard').classList.add('hidden');
    document.getElementById('registerCard').classList.add('hidden');
    document.getElementById(targetCardId).classList.remove('hidden');
}

// 1. Handle Registration Protocol
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regRole').value;
    const msgBox = document.getElementById('regMessage');

    try {
        const response = await fetch(`${AUTH_API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password, role })
        });

        if (response.ok) {
            msgBox.style.color = 'green';
            msgBox.textContent = "Registration successful! Please log in.";
            msgBox.style.display = 'block';
            document.getElementById('registerForm').reset();
            
            // Auto-swap back to login screen after 2 seconds
            setTimeout(() => toggleAuthView('loginCard'), 2000);
        } else {
            const errorText = await response.text();
            msgBox.style.color = 'red';
            msgBox.textContent = `Error: ${errorText}`;
            msgBox.style.display = 'block';
        }
    } catch (error) {
        msgBox.style.color = 'red';
        msgBox.textContent = "Gateway Connection Failed. Is the Spring Boot server running?";
        msgBox.style.display = 'block';
        console.error("Registration Error:", error);
    }
});

// 2. Handle Login & Token Management Protocol
document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const targetRole = document.getElementById('loginRole').value;

    // For a Capstone prototype using Spring HTTP Basic Auth, we store the 
    // Base64 encoded credentials to attach to future API requests if needed.
    const basicAuthToken = btoa(`${username}:${password}`);
    localStorage.setItem('dermoAuthToken', basicAuthToken);
    localStorage.setItem('dermoUserRole', targetRole);
    localStorage.setItem('dermoUsername', username);

    // Route to the appropriate isolated micro-frontend
    if (targetRole === 'PATIENT') {
        window.location.href = 'patient.html';
    } else if (targetRole === 'DOCTOR') {
        window.location.href = 'doctor.html';
    }
});

// 3. Global Logout Utility (Can be called from patient.js or doctor.js)
window.logout = function() {
    localStorage.removeItem('dermoAuthToken');
    localStorage.removeItem('dermoUserRole');
    localStorage.removeItem('dermoUsername');
    window.location.href = 'index.html';
}