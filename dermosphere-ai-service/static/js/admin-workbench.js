if (!sessionStorage.getItem('dermoAuthToken')) {
    window.location.replace('admin-login.html');
}

function logoutAdmin() {
    sessionStorage.removeItem('dermoAuthToken');
    window.location.replace('admin-login.html');
}

function switchTab(tabId, evt) {
    document.getElementById('sql-tab').style.display = tabId === 'sql-tab' ? 'block' : 'none';
    document.getElementById('matrix-tab').style.display = tabId === 'matrix-tab' ? 'block' : 'none';
    document.getElementById('sec-tab').style.display = tabId === 'sec-tab' ? 'block' : 'none';
    
    document.querySelectorAll('.nav-icon').forEach(el => el.classList.remove('active'));
    if (evt && evt.target) {
        evt.target.classList.add('active');
    }
    
    if (tabId === 'matrix-tab' && !chartsInitialized) initChartMatrix();
    if (tabId === 'sec-tab') fetchPendingRequests();
}

let isObfuscated = true;
let currentDataset = [];

function updateSyntax() {
    const text = document.getElementById('sql-input').value;
    let highlighted = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|DROP|ALTER|AND|OR|JOIN|INNER|LEFT|ON|GROUP BY|ORDER BY|LIMIT)\b/gi, '<span class="sql-keyword">$&</span>')
        .replace(/\b(COUNT|MAX|MIN|AVG|SUM)\b/gi, '<span class="sql-function">$&</span>')
        .replace(/('.*?')/g, '<span class="sql-string">$&</span>');
        
    document.getElementById('highlight-layer').innerHTML = highlighted + '<br>'; 
}

const sqlInputElem = document.getElementById('sql-input');
if (sqlInputElem) {
    sqlInputElem.addEventListener('scroll', function() {
        document.getElementById('highlight-layer').scrollTop = this.scrollTop;
        document.getElementById('highlight-layer').scrollLeft = this.scrollLeft;
    });
}

function toggleObfuscation() {
    isObfuscated = !isObfuscated;
    const btn = document.getElementById('obfuscate-btn');
    btn.innerText = `Mask Data: ${isObfuscated ? 'ON' : 'OFF'}`;
    btn.style.color = isObfuscated ? 'var(--accent-cyan)' : 'var(--accent-red)';
    btn.style.borderColor = isObfuscated ? 'var(--accent-cyan)' : 'var(--accent-red)';
    renderTable(currentDataset);
}

function obfuscateString(str) {
    if (!str || str.length < 3) return "***";
    if (str.includes('@')) {
        const parts = str.split('@');
        return parts[0].charAt(0) + "***@" + parts[1];
    }
    return str.charAt(0) + "***" + str.charAt(str.length - 1);
}

async function executeSQL() {
    const query = document.getElementById('sql-input').value;
    
    try {
        const response = await fetch('/api/v1/admin/workbench/execute-sql', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'Authorization': 'Bearer ' + sessionStorage.getItem('dermoAuthToken') 
            },
            body: JSON.stringify({ query: query })
        });
        const result = await response.json();
        
        if (response.status === 403 || response.status === 401) {
            alert("SECURITY LOCKOUT: " + (result.error || "Unauthorized Request"));
            return;
        }
        if (result.data) {
            currentDataset = result.data;
            renderTable(currentDataset);
        }
    } catch (error) { console.error("Execution failed:", error); }
}

function renderTable(dataArray) {
    const table = document.getElementById('sql-results-table');
    table.replaceChildren();
    if (!dataArray || dataArray.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.style.textAlign = 'center';
        td.style.color = '#64748b';
        td.textContent = 'No records returned.';
        tr.appendChild(td);
        table.appendChild(tr);
        return;
    }
    const headers = Object.keys(dataArray[0]);
    const headerRow = document.createElement('tr');
    headers.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h.toUpperCase();
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);
    
    dataArray.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(key => {
            let val = row[key];
            if (isObfuscated && (key.includes('name') || key.includes('email') || key.includes('ip'))) {
                val = obfuscateString(String(val));
            }
            const td = document.createElement('td');
            td.textContent = val !== null && val !== undefined ? val : 'NULL';
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
}



 