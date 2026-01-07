// history.js - Load and display user's analysis history

document.addEventListener('DOMContentLoaded', function() {
    loadUserHistory();
});

async function loadUserHistory() {
    // Show loading spinner, hide error and table
    document.getElementById('historyLoading').classList.remove('hidden');
    document.getElementById('historyError').classList.add('hidden');
    document.getElementById('historyTableContainer').classList.add('hidden');
    document.getElementById('chartsSection').classList.add('hidden');
    document.getElementById('historyInfo').classList.add('hidden');

    try {
        const response = await fetch('/api/get_entries'); // ✅ This gets LATEST 5 only
        const data = await response.json();

        if (data.success) {
            if (data.entries && data.entries.length > 0) {
                // ✅ UPDATE DOWNLOAD BUTTON TEXT WITH TOTAL COUNT
                const downloadBtn = document.getElementById('downloadCsvBtn');
                downloadBtn.disabled = false;
                downloadBtn.textContent = `📥 Download Full History (${data.total_count} records)`;
                
                // ✅ SHOW RECORD COUNT INFO
                const infoText = `Showing latest ${data.entries.length} of ${data.total_count} records`;
                document.getElementById('historyInfo').textContent = infoText;
                document.getElementById('historyInfo').classList.remove('hidden');
                
                // Display the data in the table
                displayHistoryTable(data.entries);
                // Show the table container
                document.getElementById('historyTableContainer').classList.remove('hidden');
                
                // Create the mood chart
                createMoodChart(data.entries);
                document.getElementById('chartsSection').classList.remove('hidden');
            } else {
                // No entries found
                document.getElementById('historyError').textContent = 'No journal entries found. Start by analyzing your mood!';
                document.getElementById('historyError').classList.remove('hidden');
            }
        } else {
            // API returned success: false
            if (data.message === 'User not logged in') {
                alert('Please login to view your history.');
                window.location.href = '/';
            } else {
                throw new Error(data.message || 'Could not fetch history');
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('historyError').classList.remove('hidden');
    } finally {
        // Hide loading spinner
        document.getElementById('historyLoading').classList.add('hidden');
    }
}

function displayHistoryTable(entries) {
    const tableBody = document.querySelector('#entriesTable tbody');
    tableBody.innerHTML = ''; // Clear any existing rows

    entries.forEach(entry => {
        const row = document.createElement('tr');
        
        // Format date nicely
        const date = new Date(entry['timestamp']);
        const formattedDate = date.toLocaleString();
        
        // Create journal preview (first 50 chars)
        const journalPreview = entry['journal_text'] 
            ? (entry['journal_text'].length > 50 
                ? entry['journal_text'].substring(0, 50) + '...' 
                : entry['journal_text'])
            : '—';
        
        // Get confidence values or display dash if not available
        const textConf = entry['text_confidence'] ? Math.round(entry['text_confidence'] * 100) + '%' : '—';
        const audioConf = entry['audio_confidence'] ? Math.round(entry['audio_confidence'] * 100) + '%' : '—';
        
        // ✅ Create audio player if audio exists
        let audioPlayer = '—';
        if (entry['audio_file_path']) {
            const audioUrl = `/uploads/${entry['audio_file_path']}`;
            audioPlayer = `
                <audio controls style="width: 120px; height: 30px;">
                    <source src="${audioUrl}" type="audio/wav">
                    Your browser does not support the audio element.
                </audio>
            `;
        }
        
        row.innerHTML = `
    <td>${formattedDate}</td>
    <td title="${entry['journal_text'] || ''}">${journalPreview}</td>
    <td>${entry['final_emotion'] || 'N/A'}</td>
    <td>${textConf}</td>
    <td>${audioConf}</td>
    <td>${entry['mood_score'] || 'N/A'}</td> <!-- ✅ NEW: Mood Score Column -->
    <td>${audioPlayer}</td>
        `;
        
        tableBody.appendChild(row);
    });
}
// ✅ Function to create the mood timeline chart
function createMoodChart(entries) {
    const ctx = document.getElementById('moodTimelineChart').getContext('2d');
    
    // Prepare data for the chart
    const sortedEntries = entries.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    const dates = sortedEntries.map(entry => {
        const date = new Date(entry.timestamp);
        return date.toLocaleDateString(); // Format as MM/DD/YYYY
    });
    
    const moodScores = sortedEntries.map(entry => entry.mood_score || 50);
    const emotions = sortedEntries.map(entry => entry.final_emotion || 'Unknown');
    
    // Create the chart
    const moodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Mood Score',
                data: moodScores,
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: emotions.map(emotion => {
                    // Color code points by emotion
                    const colors = {
                        'joy': '#ffdd59', 'love': '#ff6b81', 'optimism': '#a29bfe',
                        'sadness': '#74b9ff', 'fear': '#636e72', 'anger': '#ff7675',
                        'disgust': '#00b894', 'anxiety': '#fd79a8', 'default': '#00d4ff'
                    };
                    return colors[emotion.toLowerCase()] || colors['default'];
                }),
                pointBorderColor: '#ffffff',
                pointRadius: 6,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.3 // Smooth lines
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false,
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            // Add emotion labels to Y axis
                            if (value === 100) return '😄 Excellent';
                            if (value === 75) return '😊 Good';
                            if (value === 50) return '😐 Neutral';
                            if (value === 25) return '😟 Low';
                            if (value === 0) return '😔 Very Low';
                            return value;
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return `Mood: ${moodScores[index]} (${emotions[index]})`;
                        }
                    }
                }
            },
            maintainAspectRatio: false
        }
    });
}
// ✅ CSV Download Function (GETS ALL RECORDS)
async function downloadCSV() {
    try {
        // ✅ USE all=true PARAMETER TO GET ALL RECORDS
        const response = await fetch('/api/get_entries?all=true');
        const data = await response.json();
        
        if (data.success && data.entries.length > 0) {
            // Create CSV content
            let csvContent = "Date,Journal Text,Final Emotion,Text Confidence,Audio Confidence,Mood Score,Audio File\n";
            
            data.entries.forEach(entry => {
                const date = new Date(entry.timestamp).toLocaleString();
                const journal = entry.journal_text ? `"${entry.journal_text.replace(/"/g, '""')}"` : '';
                const textConf = entry.text_confidence ? (entry.text_confidence * 100) + '%' : '';
                const audioConf = entry.audio_confidence ? (entry.audio_confidence * 100) + '%' : '';
                
                csvContent += `${date},${journal},${entry.final_emotion || ''},${textConf},${audioConf},${entry.mood_score || ''},${entry.audio_file_path || ''}\n`;
            });
            
            // Create download link
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `mindmirror_full_history_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert('No records available to download.');
        }
    } catch (error) {
        console.error('Error downloading CSV:', error);
        alert('Could not download history. Please try again.');
    }
}

// ✅ Add event listener to download button
document.getElementById('downloadCsvBtn').addEventListener('click', downloadCSV);