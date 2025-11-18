// Automated Reminders for Upcoming Classes
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page that needs reminders
    const dashboard = document.querySelector('.tutor-dashboard') || 
                      document.querySelector('.student-dashboard');
    
    if (dashboard) {
        initializeReminders();
    }
    
    function initializeReminders() {
        // Check for upcoming classes every 5 minutes
        setInterval(checkUpcomingClasses, 5 * 60 * 1000);
        
        // Initial check
        checkUpcomingClasses();
        
        // Check for notifications that need to be dismissed
        checkNotifications();
    }
    
    function checkUpcomingClasses() {
        // In a real app, this would make an AJAX call to get upcoming classes
        // For now, we'll simulate the check with some hardcoded data
        
        const upcomingClasses = getUpcomingClasses();
        
        upcomingClasses.forEach(classItem => {
            const classTime = new Date(classItem.start_time);
            const now = new Date();
            const timeUntilClass = classTime - now;
            
            // Check if class is within 24 hours
            if (timeUntilClass > 0 && timeUntilClass < 24 * 60 * 60 * 1000) {
                // Check if we've already shown a reminder for this class
                if (!localStorage.getItem(`reminder_shown_${classItem.id}`)) {
                    showUpcomingClassReminder(classItem);
                    localStorage.setItem(`reminder_shown_${classItem.id}`, 'true');
                }
            }
        });
    }
    
    function showUpcomingClassReminder(classItem) {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed top-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const classTime = new Date(classItem.start_time);
        const formattedTime = classTime.toLocaleString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        toast.innerHTML = `
            <div class="toast-header bg-info text-white">
                <strong class="me-auto">Upcoming Class</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                <p class="mb-1">You have a ${classItem.type} class coming up!</p>
                <p class="mb-0"><strong>${classItem.student_name}</strong> - ${formattedTime}</p>
                <div class="mt-2">
                    <a href="${classItem.details_link}" class="btn btn-sm btn-primary">View Details</a>
                    <button class="btn btn-sm btn-secondary ms-2" onclick="dismissReminder('${classItem.id}')">Dismiss</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 30000);
        
        // Play a subtle sound notification
        playNotificationSound();
    }
    
    function playNotificationSound() {
        // Create a subtle notification sound
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSl+zPLaizsIG2m98OScTgwOUarm7blmFgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
    
    function dismissReminder(classId) {
        // Remove the toast
        const toast = document.querySelector(`[data-class-id="${classId}"]`);
        if (toast) {
            toast.remove();
        }
        
        // Mark as dismissed
        localStorage.setItem(`reminder_dismissed_${classId}`, 'true');
    }
    
    function checkNotifications() {
        // Check for notifications that need to be shown
        const notifications = getNotifications();
        
        notifications.forEach(notification => {
            // Check if notification is due to be shown
            const showTime = new Date(notification.show_time);
            const now = new Date();
            
            if (now >= showTime && !localStorage.getItem(`notification_shown_${notification.id}`)) {
                showNotification(notification);
                localStorage.setItem(`notification_shown_${notification.id}`, 'true');
            }
        });
    }
    
    function showNotification(notification) {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed top-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        let iconClass = 'fas fa-info-circle';
        let bgClass = 'bg-info';
        
        if (notification.type === 'warning') {
            iconClass = 'fas fa-exclamation-triangle';
            bgClass = 'bg-warning';
        } else if (notification.type === 'error') {
            iconClass = 'fas fa-exclamation-circle';
            bgClass = 'bg-danger';
        } else if (notification.type === 'success') {
            iconClass = 'fas fa-check-circle';
            bgClass = 'bg-success';
        }
        
        toast.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">${notification.title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${notification.message}
                ${notification.action ? `
                    <div class="mt-2">
                        <a href="${notification.action.link}" class="btn btn-sm btn-primary">${notification.action.text}</a>
                    </div>
                ` : ''}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 10000);
    }
    
    // Helper functions to get upcoming classes and notifications
    // In a real app, these would make AJAX calls to the server
    
    function getUpcomingClasses() {
        // This would normally be fetched from the server
        return [
            {
                id: 1,
                type: 'Demo',
                student_name: 'John Doe',
                start_time: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
                details_link: '/tutor/booking-details/1'
            },
            {
                id: 2,
                type: 'Regular Class',
                student_name: 'Jane Smith',
                start_time: new Date(Date.now() + 6 * 60 * 60 * 1000), // 6 hours from now
                details_link: '/tutor/booking-details/2'
            }
        ];
    }
    
    function getNotifications() {
        // This would normally be fetched from the server
        return [
            {
                id: 1,
                type: 'info',
                title: 'System Update',
                message: 'A new feature has been added to the platform.',
                show_time: new Date(Date.now() + 30 * 60 * 1000), // 30 minutes from now
                action: {
                    text: 'Learn More',
                    link: '/help/new-features'
                }
            }
        ];
    }
    
    // Make dismissReminder function global
    window.dismissReminder = dismissReminder;
});

// CSS for reminder styling
const reminderStyles = `
    .toast {
        min-width: 300px;
        max-width: 500px;
    }
    
    .toast-header {
        font-weight: 600;
    }
    
    .toast-body {
        font-size: 0.9rem;
    }
    
    .toast-body .btn-sm {
        font-size: 0.8rem;
    }
`;

// Add the styles to the document
const styleSheet = document.createElement('style');
styleSheet.textContent = reminderStyles;
document.head.appendChild(styleSheet);