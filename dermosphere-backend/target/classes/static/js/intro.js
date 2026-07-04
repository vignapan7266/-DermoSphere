document.addEventListener("DOMContentLoaded", () => {
    const actionPanel = document.getElementById('actionPanel');
    const skipBtn = document.getElementById('skipBtn');
    
    // Simulating system initialization time
    let introTimeout = setTimeout(showActions, 4500);

    function showActions() {
        actionPanel.classList.add('visible');
        skipBtn.style.opacity = '0';
        skipBtn.style.pointerEvents = 'none';
    }

    function skipIntro() {
        clearTimeout(introTimeout);
        showActions();
        // Immediately complete SVG drawing
        document.querySelectorAll('.svg-path').forEach(el => el.style.animationDuration = '0.1s');
    }

    skipBtn.addEventListener('click', skipIntro);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === 'Escape') skipIntro();
    });
});