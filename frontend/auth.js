// Auth.js - Authentication logic (CORRECTED VERSION)

let generatedUserId = null;

// Show registration modal
function showRegistration() {
    // Generate user ID first
    generateUserId();
    document.getElementById('registrationModal').classList.remove('hidden');
}

// Hide registration modal
function hideRegistration() {
    document.getElementById('registrationModal').classList.add('hidden');
}

// Show recovery modal
function showRecovery() {
    document.getElementById('recoveryModal').classList.remove('hidden');
}

// Hide recovery modal  
function hideRecovery() {
    document.getElementById('recoveryModal').classList.add('hidden');
}

// Generate unique user ID
async function generateUserId() {
    try {
        const response = await fetch('/api/generate_user_id');
        const data = await response.json();
        
        if (data.success) {
            generatedUserId = data.user_id;
            document.getElementById('generatedUserId').textContent = generatedUserId;
        } else {
            alert('Error generating user ID');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not connect to server');
    }
}

// Handle registration form submission
// Handle registration form submission
async function handleRegistration(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!fullName || !email) {
        alert('Please fill in all fields');
        return;
    }
    
    if (!generatedUserId) {
        alert('Please wait for user ID generation');
        return;
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: generatedUserId,
                full_name: fullName,
                email: email
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // ✅ Store user info in sessionStorage for the profile page
            sessionStorage.setItem('userName', fullName);
            sessionStorage.setItem('userEmail', email);
            sessionStorage.setItem('userId', generatedUserId);
            
            // ✅ Use redirect from server or default to profile
            window.location.href = data.redirect || '/profile';
        } else {
            alert('Registration failed: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not connect to server');
    }
}

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const userId = document.getElementById('userIdInput').value.trim().toUpperCase();
    
    if (!userId) {
        alert('Please enter your User ID');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // ✅ Store user info in sessionStorage for the profile page
            sessionStorage.setItem('userName', data.full_name);
            sessionStorage.setItem('userEmail', data.email);
            sessionStorage.setItem('userId', data.user_id);
            
            // ✅ Use redirect from server or default to profile
            window.location.href = data.redirect || '/profile';
        } else {
            alert('Login failed: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not connect to server');
    }
}
// Handle recovery form submission
async function handleRecovery(event) {
    event.preventDefault();
    
    const email = document.getElementById('recoveryEmail').value.trim();
    
    if (!email) {
        alert('Please enter your email');
        return;
    }
    
    try {
        const response = await fetch('/api/recover_id', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Your User ID is: ${data.user_id}\nYou can now login with this ID.`);
            hideRecovery();
        } else {
            alert('Recovery failed: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Could not connect to server');
    }
}

// ✅ REMOVED the automatic redirect function that was causing the loop