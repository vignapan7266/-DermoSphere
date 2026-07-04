let currentCaptchaStr = "";

function generateCaptcha() {
    const canvas = document.getElementById('captchaCanvas');
    if (!canvas) return; // Prevent errors on non-auth pages
    
    const ctx = canvas.getContext('2d');
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // Removed similar looking I, O, 1, 0
    currentCaptchaStr = "";
    
    // Clear canvas and set background
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw severe background noise (dots)
    for (let i = 0; i < 100; i++) {
        ctx.fillStyle = `rgba(${Math.random()*255}, ${Math.random()*255}, ${Math.random()*255}, 0.5)`;
        ctx.beginPath();
        ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, Math.random() * 2, 0, Math.PI * 2);
        ctx.fill();
    }

    // Draw interference lines
    for (let i = 0; i < 5; i++) {
        ctx.strokeStyle = `rgba(${Math.random()*255}, ${Math.random()*255}, ${Math.random()*255}, 0.8)`;
        ctx.lineWidth = Math.random() * 2;
        ctx.beginPath();
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.stroke();
    }

    // Generate 5-character string with rotation and varying fonts
    for (let i = 0; i < 5; i++) {
        const char = chars.charAt(Math.floor(Math.random() * chars.length));
        currentCaptchaStr += char;
        
        ctx.font = `${24 + Math.random() * 8}px "Courier New", monospace`;
        ctx.fillStyle = "#0b0f19";
        
        ctx.save();
        ctx.translate(20 + i * 25, 30 + (Math.random() * 10 - 5));
        ctx.rotate((Math.random() * 0.4) - 0.2); // Random rotation between -0.2 and 0.2 rads
        ctx.fillText(char, 0, 0);
        ctx.restore();
    }
}

// Validate function to be called externally
function validateCaptcha(input) {
    return input.toUpperCase() === currentCaptchaStr;
}

// Auto-init if DOM is ready
document.addEventListener("DOMContentLoaded", generateCaptcha);