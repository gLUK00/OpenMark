/**
 * OpenMark - History JavaScript
 */

let currentPage = 0;
const pageSize = 10;

async function loadHistory(offset = 0) {
    try {
        const result = await Auth.apiRequest(`/api/history?limit=${pageSize}&offset=${offset}`);
        
        if (result && result.success) {
            renderHistory(result.history);
            renderPagination(result.total, offset);
            currentPage = Math.floor(offset / pageSize);
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(history) {
    const tbody = document.getElementById('historyBody');
    
    if (history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No history found</td></tr>';
        return;
    }
    
    tbody.innerHTML = history.map(item => {
        const date = new Date(item.timestamp);
        const duration = formatDuration(item.duration_seconds);
        
        return `
            <tr>
                <td>${item.document_name || item.document_id}</td>
                <td>${date.toLocaleString()}</td>
                <td>${item.ip_address}</td>
                <td>${duration}</td>
            </tr>
        `;
    }).join('');
}

function renderPagination(total, currentOffset) {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(total / pageSize);
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    if (currentOffset > 0) {
        html += `<button onclick="loadHistory(${currentOffset - pageSize})">Previous</button>`;
    }
    
    // Page numbers
    for (let i = 0; i < totalPages; i++) {
        const offset = i * pageSize;
        const isActive = offset === currentOffset ? 'active' : '';
        html += `<button class="${isActive}" onclick="loadHistory(${offset})">${i + 1}</button>`;
    }
    
    // Next button
    if (currentOffset + pageSize < total) {
        html += `<button onclick="loadHistory(${currentOffset + pageSize})">Next</button>`;
    }
    
    pagination.innerHTML = html;
}

function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '-';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
}

document.addEventListener('DOMContentLoaded', () => {
    loadHistory(0);
});
