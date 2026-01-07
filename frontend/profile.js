// profile.js - Handle profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
});

function loadUserProfile() {
    // Load user data from session (you might want to fetch from server instead)
    const userName = sessionStorage.getItem('userName') || 'User';
    const userEmail = sessionStorage.getItem('userEmail') || '';
    const userId = sessionStorage.getItem('userId') || '';
    
    document.getElementById('userName').textContent = userName;
    document.getElementById('userIdDisplay').textContent = userId;
    document.getElementById('userEmailDisplay').textContent = userEmail;
    document.getElementById('editName').value = userName;
    document.getElementById('editEmail').value = userEmail;
    
    // Set join date (you'll need to get this from your database later)
    document.getElementById('joinDate').textContent = new Date().toLocaleDateString();
}

function toggleEdit() {
    document.getElementById('profileInfo').classList.add('hidden');
    document.getElementById('profileForm').classList.remove('hidden');
}

function cancelEdit() {
    document.getElementById('profileForm').classList.add('hidden');
    document.getElementById('profileInfo').classList.remove('hidden');
    // Reset form values
    loadUserProfile();
}

async function updateProfile(event) {
    event.preventDefault();
    
    const newName = document.getElementById('editName').value.trim();
    const newEmail = document.getElementById('editEmail').value.trim();
    
    try {
        const response = await fetch('/api/update_profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                full_name: newName,
                email: newEmail
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update displayed info
            document.getElementById('userName').textContent = newName;
            document.getElementById('userEmailDisplay').textContent = newEmail;
            
            // Update session storage
            sessionStorage.setItem('userName', newName);
            sessionStorage.setItem('userEmail', newEmail);
            
            // Show success message
            showStatus('✅ Profile updated successfully!', 'success');
            
            // Switch back to view mode
            cancelEdit();
        } else {
            showStatus('❌ ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showStatus('❌ Could not update profile', 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('profileStatus');
    statusDiv.textContent = message;
    statusDiv.className = type === 'success' ? 'success-message' : 'error-message';
    statusDiv.classList.remove('hidden');
    
    setTimeout(() => {
        statusDiv.classList.add('hidden');
    }, 3000);
}