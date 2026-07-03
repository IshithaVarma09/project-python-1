// app.js
document.addEventListener("DOMContentLoaded", () => {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.transition = "opacity 0.5s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000);
    }

    // Smart Reminders System
    function fetchAndShowReminders() {
        if (!document.getElementById('toast-container')) return; // Ensure we are logged in
        fetch('/api/reminders')
            .then(res => {
                if(res.ok) return res.json();
                throw new Error("Cannot fetch reminders");
            })
            .then(data => {
                if (data && data.reminders && data.reminders.length > 0) {
                    data.reminders.forEach((reminder, index) => {
                        setTimeout(() => showToast(reminder), index * 2000);
                    });
                }
            })
            .catch(err => console.log("Smart Alerts idle.", err));
    }

    function showToast(reminder) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `smart-toast ${reminder.type}`;
        
        let icon = "🔔";
        if (reminder.type === 'danger') icon = "🚨";
        if (reminder.type === 'warning') icon = "⏳";
        if (reminder.type === 'info') icon = "💡";
        
        let title = "Smart Reminder";
        if (reminder.message.includes("Prep")) title = "Exam Strategy";
        else if (reminder.message.includes("due") || reminder.message.includes("Overdue")) title = "Task Deadline";
        
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <h4>${title}</h4>
                <p>${reminder.message}</p>
            </div>
        `;
        
        container.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Remove after 6 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400); // Wait for transition
        }, 6000);
    }

    // Trigger shortly after load
    setTimeout(fetchAndShowReminders, 2000);
    
    // Simulate "time to time" alerts by checking every 45 seconds
    setInterval(fetchAndShowReminders, 45000);
});
