/**
 * OpenMark - Statistics JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const result = await Auth.apiRequest('/api/statistics');
        
        if (result && result.success) {
            const stats = result.statistics;
            
            document.getElementById('documentsViewed').textContent = stats.documents_viewed || 0;
            document.getElementById('notesCreated').textContent = stats.notes_created || 0;
            document.getElementById('highlightsCreated').textContent = stats.highlights_created || 0;
            
            if (stats.last_activity) {
                const date = new Date(stats.last_activity);
                document.getElementById('lastActivity').textContent = date.toLocaleString();
            } else {
                document.getElementById('lastActivity').textContent = 'Never';
            }
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
});
