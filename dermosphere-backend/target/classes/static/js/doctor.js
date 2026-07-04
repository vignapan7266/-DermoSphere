
const BACKEND_URL = '/api/v1/triage';
const AI_SERVICE_URL = 'http://localhost:8000';

async function loadFeed() {
    const container = document.getElementById('queueContainer');
    
    // 1. Inject UI Skeleton Loaders instantly
    container.innerHTML = `
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
    `;

    try {
        // Fetches from the lightning-fast Caffeine RAM cache
        const response = await fetch(`${BACKEND_URL}/queue`);
        if (!response.ok) throw new Error("Gateway failed to fetch feed.");
        
        const scans = await response.json();
        container.innerHTML = '';

        if (scans.length === 0) {
            container.innerHTML = '<p>The network feed is currently empty.</p>';
            return;
        }

        // 2. Render the Feed Cards
        scans.forEach(scan => {
            const isHigh = scan.triageTier === 'HIGH';
            const imgClass = isHigh ? 'feed-thumbnail high-risk' : 'feed-thumbnail';
            const confidence = (scan.confidenceScore * 100).toFixed(1);
            
            const card = document.createElement('div');
            card.className = 'feed-card';
            
            card.innerHTML = `
                <img src="${AI_SERVICE_URL}${scan.heatmapPath}" class="${imgClass}" alt="Lesion Scan">
                <div class="feed-content">
                    <h4 style="margin:0 0 0.5rem 0; color: ${isHigh ? 'red' : 'inherit'}">
                        Prediction: ${scan.predictedClass.toUpperCase()}
                    </h4>
                    <p style="margin:0; font-size: 0.9rem; color: #666;">AI Confidence: ${confidence}%</p>
                    <p style="margin:0.2rem 0; font-size: 0.8rem; color: #999;">Scan #${scan.id} | Uploaded: ${new Date(scan.scannedAt).toLocaleDateString()}</p>
                    
                    <div class="engagement-bar">
                        <div>
                            <span style="color: green; font-weight: bold;">↑ ${scan.upvotes}</span>
                            <span style="color: red; font-weight: bold; margin-left: 10px;">↓ ${scan.downvotes}</span>
                        </div>
                        <div>
                            <button class="btn btn-primary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="engage(${scan.id}, 'AGREE')">👍</button>
                            <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="engage(${scan.id}, 'DISAGREE')">👎</button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (error) {
        container.innerHTML = `<p style="color: red;">Feed Offline: ${error.message}</p>`;
    }
}

async function engage(scanId, interactionType) {
    try {
        const response = await fetch(`${BACKEND_URL}/feedback/${scanId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback: interactionType })
        });
        
        if (response.ok) {
            // Re-render feed smoothly to show updated upvote/downvote counts
            loadFeed(); 
        }
    } catch (error) {
        console.error("Engagement tracking failed:", error);
    }
}

window.onload = loadFeed;