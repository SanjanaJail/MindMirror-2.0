let mediaRecorder;
let recordedChunks = [];
let recordedBlob = null;

// 🎙 Start Recording
document.getElementById("startRec").addEventListener("click", async () => {
    recordedChunks = [];
    recordedBlob = null;
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();

        document.getElementById("recStatus").textContent = "🎙 Recording...";
        document.getElementById("startRec").disabled = true;
        document.getElementById("stopRec").disabled = false;

        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) recordedChunks.push(e.data);
        };
    } catch (err) {
        alert("❌ Microphone access denied!");
    }
});

// ⏹ Stop Recording
document.getElementById("stopRec").addEventListener("click", () => {
    mediaRecorder.stop();
    mediaRecorder.onstop = () => {
        recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
        document.getElementById("recStatus").innerHTML = "✅ Recording saved (Ready to analyze)";
        document.getElementById("startRec").disabled = false;
        document.getElementById("stopRec").disabled = true;

        // 🎧 Add a temporary playback for user
        const audioURL = URL.createObjectURL(recordedBlob);
        addPlayback(audioURL);
    };
});

// 🎧 Function to dynamically add audio player
function addPlayback(url) {
    let existing = document.getElementById("playRecorded");
    if (existing) existing.remove(); // remove old player if any
    const player = document.createElement("audio");
    player.id = "playRecorded";
    player.controls = true;
    player.src = url;
    player.style.marginTop = "10px";
    document.querySelector(".recorder").appendChild(player);
}

// ✅ Show notification popup
function showNotification(message, isSuccess = true) {
    const oldNotification = document.getElementById('storageNotification');
    if (oldNotification) {
        oldNotification.remove();
    }

    const notification = document.createElement('div');
    notification.id = 'storageNotification';
    notification.innerHTML = isSuccess ? '✅ ' : '❌ ';
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    notification.appendChild(messageSpan);
    
    notification.style.position = 'fixed';
    notification.style.top = '50%';
    notification.style.left = '50%';
    notification.style.transform = 'translate(-50%, -50%)';
    notification.style.padding = '20px 30px';
    notification.style.borderRadius = '15px';
    notification.style.color = 'white';
    notification.style.fontWeight = 'bold';
    notification.style.fontSize = '1.2rem';
    notification.style.zIndex = '10000';
    notification.style.boxShadow = '0 6px 25px rgba(0,0,0,0.4)';
    notification.style.textAlign = 'center';
    notification.style.minWidth = '300px';
    notification.style.opacity = '0';
    notification.style.transition = 'all 0.5s ease';

    if (isSuccess) {
        notification.style.background = 'linear-gradient(135deg, #00b894, #00d4ff)';
        notification.style.border = '2px solid #00ffcc';
    } else {
        notification.style.background = 'linear-gradient(135deg, #ff4757, #ff6b81)';
        notification.style.border = '2px solid #ff7675';
    }

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, -50%) scale(1.05)';
        setTimeout(() => {
            notification.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 150);
    }, 10);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -50%) scale(0.8)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 500);
    }, 3000);
}

// 🔍 Analyze Mood
document.getElementById("analyzeBtn").addEventListener("click", async () => {
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("results").classList.add("hidden");
    document.getElementById("therapySection").classList.add("hidden");
    
    const journal = document.getElementById("journal").value.trim();
    const audioFile = document.getElementById("audio").files[0];
    const formData = new FormData();

    if (journal) {
        formData.append("text", journal);
    }

    if (recordedBlob) {
        const audioFile = new File([recordedBlob], "live_recording.webm", { type: "audio/webm" });
        formData.append("audio", audioFile);
    } else if (audioFile) {
        formData.append("audio", audioFile);
    }

    if (!journal && !recordedBlob && !audioFile) {
        alert("⚠️ Please provide at least journal text or an audio input.");
        document.getElementById("loading").classList.add("hidden");
        return;
    }

    try {
        const res = await fetch(`${window.location.origin}/analyze`, {
            method: "POST",
            body: formData
        });
        
        const data = await res.json();

        if (data.error && data.error === "User not logged in") {
            alert("Session expired. Please login again.");
            window.location.href = '/';
            return;
        }
        
        if (data.audio_url) {
            addPlayback(data.audio_url);
        }

        document.getElementById("textEmotion").textContent = data.Text_Emotion || "Not provided";
        document.getElementById("textConf").textContent = data.Text_Conf ?? "-";
        document.getElementById("audioEmotion").textContent = data.Audio_Emotion || "Not provided";
        document.getElementById("audioConf").textContent = data.Audio_Conf ?? "-";
        document.getElementById("finalMood").textContent = data.Final_Emotion || "Uncertain";
        document.getElementById("results").classList.remove("hidden");

        // Show therapy button
        document.getElementById("getTherapyBtn").style.display = 'block';

        if (data.saved_to_db) {
            showNotification('✅ Data successfully stored!', true);
        } else {
            showNotification('❌ Could not save data. Please try again.', false);
        }

    } catch (err) {
        console.error("Error:", err);
        alert("❌ Could not connect to backend. Make sure Flask is running.");
    }
    finally {
        document.getElementById("loading").classList.add("hidden");
    }
});

// 🎯 Therapeutic Intervention Functions
document.getElementById('getTherapyBtn').addEventListener('click', async () => {
    const currentEmotion = document.getElementById('finalMood').textContent.toLowerCase();
    
    if (!currentEmotion || currentEmotion === 'uncertain') {
        alert('Please analyze your mood first to get personalized therapy recommendations.');
        return;
    }
    
    try {
        const response = await fetch('/api/get_therapy_recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                emotion: currentEmotion
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayTherapyPlan(data.therapy_plan);
            document.getElementById('therapySection').classList.remove('hidden');
        } else {
            alert('Could not generate therapy plan. Please try again.');
        }
    } catch (error) {
        console.error('Error getting therapy plan:', error);
        alert('Error connecting to server. Please try again.');
    }
});

function displayTherapyPlan(plan) {
    // Display immediate relief
    const immediateRelief = document.getElementById('immediateRelief');
    immediateRelief.innerHTML = '';
    
    if (plan.immediate_relief && plan.immediate_relief.length > 0) {
        plan.immediate_relief.forEach(item => {
            immediateRelief.innerHTML += createTherapyItemHTML(item);
        });
    } else {
        immediateRelief.innerHTML = '<p>No immediate relief items found. Try deep breathing for 2 minutes.</p>';
    }
    
    // Display daily practices
    const dailyPractices = document.getElementById('dailyPractices');
    dailyPractices.innerHTML = '';
    
    if (plan.daily_practices && plan.daily_practices.length > 0) {
        plan.daily_practices.forEach(item => {
            dailyPractices.innerHTML += createTherapyItemHTML(item);
        });
    } else {
        dailyPractices.innerHTML = '<p>No daily practices found. Try a 10-minute walk.</p>';
    }
    
    // Display lifestyle tips
    const lifestyleTips = document.getElementById('lifestyleTips');
    lifestyleTips.innerHTML = '';
    
    if (plan.lifestyle_recommendations && plan.lifestyle_recommendations.length > 0) {
        plan.lifestyle_recommendations.forEach(item => {
            lifestyleTips.innerHTML += `
                <div class="therapy-item lifestyle">
                    <strong>${item.category.toUpperCase()}:</strong> ${item.recommendation}
                    <br><small>⏱ ${item.duration} • 🎯 ${item.difficulty}</small>
                    <br><small>🔬 ${item.scientific_basis}</small>
                </div>
            `;
        });
    }
    
    // Display therapeutic insight
    const insight = document.getElementById('therapeuticInsight');
    if (plan.therapeutic_insight) {
        insight.innerHTML = `
            <div class="insight-card">
                <h4>${plan.therapeutic_insight.title}</h4>
                <p>${plan.therapeutic_insight.message}</p>
                <div class="action-tip">💡 ${plan.therapeutic_insight.action}</div>
            </div>
        `;
    }
}

function createTherapyItemHTML(item) {
    return `
        <div class="therapy-item">
            <h4>${item.title}</h4>
            <p>${item.description}</p>
            <div class="therapy-meta">
                <span class="duration">⏱ ${item.duration_minutes} min</span>
                <span class="intensity">⚡ ${item.intensity_level}</span>
                <span class="type">🎵 ${item.content_type}</span>
            </div>
            ${item.content_url ? `<a href="${item.content_url}" target="_blank" class="content-link">▶️ Watch/Listen</a>` : ''}
            <div class="scientific-basis">🔬 ${item.scientific_basis}</div>
        </div>
    `;
}

// ✅ Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}