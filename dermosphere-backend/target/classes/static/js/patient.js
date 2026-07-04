// DO NOT CHANGE THESE. They must point to the separate Python Microservice.
const AI_WS_URL = 'ws://localhost:8000/api/v1/triage/ws-predict';
const AI_STATIC_URL = 'http://localhost:8000';
let metricsChart = null; // Store chart instance for memory management

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('lesionImage');
    if (!fileInput.files[0]) return;
    
    const file = fileInput.files[0];
    const btn = document.getElementById('uploadBtn');
    
    // Reset UI State for new upload
    btn.disabled = true;
    btn.textContent = "Processing...";
    document.getElementById('resultCard').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('progressConsole').style.display = 'block';
    
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    try {
        progressText.innerHTML = "> Compressing image locally via HTML5 Canvas...<br>";
        
        // 1. Client-Side Image Compression
        const compressedBlob = await compressImage(file, 224, 224);
        
        // 2. Open WebSocket to Python Inference Engine
        const ws = new WebSocket(AI_WS_URL);
        
        ws.onopen = () => {
            progressText.innerHTML += "> Socket open. Transmitting encrypted byte array...<br>";
            ws.send(compressedBlob); 
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.error) {
                alert("AI Engine Error: " + data.error);
                ws.close();
                return;
            }
            
            if (data.step) {
                // Update Console and Progress Bar
                progressBar.style.width = `${data.progress}%`;
                progressText.innerHTML += `> [${data.progress}%] ${data.message}<br>`;
                // Auto-scroll console
                const consoleDiv = document.getElementById('progressConsole');
                consoleDiv.scrollTop = consoleDiv.scrollHeight;
            }
            
            if (data.status === "success") {
                renderFinalResults(data);
                ws.close();
            }
        };
        
        ws.onclose = () => {
            btn.disabled = false;
            btn.textContent = "Initialize AI Inference Pipeline";
        };

    } catch (error) {
        alert("System error: " + error.message);
        btn.disabled = false;
        btn.textContent = "Initialize AI Inference Pipeline";
    }
});

// Utility: HTML5 Canvas Image Compression
function compressImage(file, maxWidth, maxHeight) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = maxWidth;
            canvas.height = maxHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, maxWidth, maxHeight);
            // Export as JPEG at 80% quality to ensure blazing fast WebSocket transmission
            canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.8); 
        };
        img.onerror = error => reject(error);
    });
}

// Utility: Render UI components and Chart.js Interactive Line Graph
function renderFinalResults(data) {
    document.getElementById('resultCard').style.display = 'block';
    
    // Core details
    document.getElementById('resClass').textContent = data.prediction.toUpperCase();
    
    const tierSpan = document.getElementById('resTier');
    tierSpan.textContent = data.triage_tier;
    tierSpan.style.color = data.triage_tier === 'HIGH' ? 'var(--clr-danger)' : 'var(--clr-success)';
    
    // Grad-CAM mapping
    document.getElementById('resHeatmap').src = `${AI_STATIC_URL}${data.heatmap_path}`;
    
    // Advanced Details: Severity and Layers
    document.getElementById('resSeverity').innerHTML = `${data.severity_score} <span style="font-size: 1rem; color: #888;">/ 100</span>`;
    
    const layerContainer = document.getElementById('layerIndicator');
    layerContainer.innerHTML = '';
    // Generate 5 layer blocks, colorizing them based on calculated penetration
    for(let i = 0; i < 5; i++) {
        const div = document.createElement('div');
        div.className = `skin-layer ${i < data.skin_layers_penetrated ? 'penetrated' : ''}`;
        layerContainer.appendChild(div);
    }
    
    // Initialize or Update Interactive Chart.js Matrix
    if (metricsChart) {
        metricsChart.destroy(); // Clear previous canvas instance
    }
    
    const ctx = document.getElementById('metricsChart').getContext('2d');
    metricsChart = new Chart(ctx, {
        type: 'line', // Line graph provides a better longitudinal/scientific feel
        data: {
            labels: Object.keys(data.metrics).map(k => k.toUpperCase()),
            datasets: [{
                label: 'AI Diagnostic Probability (%)',
                data: Object.values(data.metrics).map(v => (v * 100).toFixed(2)),
                backgroundColor: 'rgba(0, 240, 255, 0.1)', // Fills under the curve
                borderColor: 'rgba(0, 240, 255, 1)',
                borderWidth: 2,
                pointBackgroundColor: '#0b0f19',
                pointBorderColor: 'rgba(0, 240, 255, 1)',
                pointRadius: 4,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.3 // Smooth curving
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index', // Allows the crosshair cursor to snap to nearest data point
                intersect: false,
            },
            plugins: {
                tooltip: {
                    backgroundColor: 'rgba(11, 15, 25, 0.95)',
                    titleFont: { size: 14, family: 'sans-serif' },
                    bodyFont: { size: 13, family: 'Courier New' },
                    padding: 12,
                    borderColor: 'rgba(0, 240, 255, 0.5)',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `Confidence: ${context.parsed.y}%`;
                        }
                    }
                },
                legend: { display: false } // Hide legend for cleaner look
            },
            scales: { 
                y: { 
                    beginAtZero: true, 
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}