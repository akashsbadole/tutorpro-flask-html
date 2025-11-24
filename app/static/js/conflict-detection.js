// Conflict Detection for Overlapping Bookings
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with booking or demo scheduling
    const scheduleForm = document.getElementById('scheduleForm') || 
                         document.getElementById('rescheduleForm') || 
                         document.getElementById('bookingForm');
    
    if (scheduleForm) {
        initializeConflictDetection();
    }
    
    function initializeConflictDetection() {
        const dateInput = document.getElementById('scheduled_date') || 
                         document.getElementById('new_scheduled_date');
        const timeInput = document.getElementById('scheduled_time') || 
                         document.getElementById('new_scheduled_time');
        const durationInput = document.getElementById('duration_minutes') || 
                            document.getElementById('new_duration_minutes');
        
        if (dateInput && timeInput && durationInput) {
            // Add event listeners for real-time conflict detection
            dateInput.addEventListener('change', checkForConflicts);
            timeInput.addEventListener('change', checkForConflicts);
            durationInput.addEventListener('change', checkForConflicts);
            
            // Initial check
            checkForConflicts();
        }
    }
    
    function checkForConflicts() {
        const dateInput = document.getElementById('scheduled_date') || 
                         document.getElementById('new_scheduled_date');
        const timeInput = document.getElementById('scheduled_time') || 
                         document.getElementById('new_scheduled_time');
        const durationInput = document.getElementById('duration_minutes') || 
                            document.getElementById('new_duration_minutes');
        
        if (!dateInput || !timeInput || !durationInput) {
            return;
        }
        
        const selectedDate = dateInput.value;
        const selectedTime = timeInput.value;
        const duration = parseInt(durationInput.value) || 60; // Default to 60 minutes
        
        if (!selectedDate || !selectedTime) {
            clearConflictMessages();
            return;
        }
        
        // Parse the selected date and time
        const selectedDateTime = new Date(`${selectedDate}T${selectedTime}`);
        const endTime = new Date(selectedDateTime.getTime() + duration * 60000);
        
        // Get the current time for comparison
        const now = new Date();
        
        // Check if the selected time is in the past
        if (selectedDateTime < now) {
            showConflictMessage('Selected date and time must be in the future.');
            return;
        }
        
        // Check for minimum advance booking (e.g., 24 hours)
        const minAdvanceHours = 24;
        const minAdvanceTime = new Date(now.getTime() + minAdvanceHours * 60 * 60 * 1000);
        
        if (selectedDateTime < minAdvanceTime) {
            showConflictMessage(`Bookings must be scheduled at least ${minAdvanceHours} hours in advance.`);
            return;
        }
        
        // Check for conflicts with existing bookings
        checkBookingConflicts(selectedDateTime, endTime);
        
        // Check for conflicts with existing demos
        checkDemoConflicts(selectedDateTime, endTime);
        
        // Check business hours
        checkBusinessHours(selectedDateTime, endTime);
    }
    
    function checkBookingConflicts(startTime, endTime) {
        // In a real app, this would make an AJAX call to get existing bookings
        // For now, we'll simulate the check with some hardcoded data
        
        const existingBookings = getExistingBookings();
        
        for (const booking of existingBookings) {
            const bookingStart = new Date(booking.start_time);
            const bookingEnd = new Date(booking.end_time);
            
            if (isTimeOverlap(startTime, endTime, bookingStart, bookingEnd)) {
                showConflictMessage(`Conflict detected with existing booking: ${booking.student_name} from ${bookingStart.toLocaleTimeString()} to ${bookingEnd.toLocaleTimeString()}.`);
                return;
            }
        }
    }
    
    function checkDemoConflicts(startTime, endTime) {
        // In a real app, this would make an AJAX call to get existing demos
        // For now, we'll simulate the check with some hardcoded data
        
        const existingDemos = getExistingDemos();
        
        for (const demo of existingDemos) {
            const demoStart = new Date(demo.start_time);
            const demoEnd = new Date(demo.end_time);
            
            if (isTimeOverlap(startTime, endTime, demoStart, demoEnd)) {
                showConflictMessage(`Conflict detected with existing demo: ${demo.student_name} from ${demoStart.toLocaleTimeString()} to ${demoEnd.toLocaleTimeString()}.`);
                return;
            }
        }
    }
    
    function checkBusinessHours(startTime, endTime) {
        // Get the day of the week (0 = Sunday, 1 = Monday, etc.)
        const dayOfWeek = startTime.getDay();
        
        // Define business hours (Monday to Friday)
        const businessHours = {
            1: { start: 9, end: 18 }, // Monday
            2: { start: 9, end: 18 }, // Tuesday
            3: { start: 9, end: 18 }, // Wednesday
            4: { start: 9, end: 18 }, // Thursday
            5: { start: 9, end: 18 }, // Friday
        };
        
        // Check if it's a weekend
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            showConflictMessage('Bookings are not available on weekends.');
            return;
        }
        
        // Get business hours for the selected day
        const hours = businessHours[dayOfWeek];
        
        if (!hours) {
            showConflictMessage('No business hours available for the selected day.');
            return;
        }
        
        // Check if the booking is within business hours
        const bookingStartHour = startTime.getHours();
        const bookingEndHour = endTime.getHours();
        
        if (bookingStartHour < hours.start || bookingEndHour > hours.end) {
            showConflictMessage(`Bookings must be between ${hours.start}:00 and ${hours.end}:00 on weekdays.`);
            return;
        }
    }
    
    function isTimeOverlap(start1, end1, start2, end2) {
        return start1 < end2 && end1 > start2;
    }
    
    function showConflictMessage(message) {
        // Remove any existing conflict messages
        clearConflictMessages();
        
        // Create a new conflict message
        const conflictDiv = document.createElement('div');
        conflictDiv.className = 'alert alert-warning alert-dismissible fade show';
        conflictDiv.setAttribute('role', 'alert');
        conflictDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Conflict Detected:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert the conflict message before the form
        const form = document.getElementById('scheduleForm') || 
                    document.getElementById('rescheduleForm') || 
                    document.getElementById('bookingForm');
        
        form.parentNode.insertBefore(conflictDiv, form);
        
        // Disable the submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add('disabled');
        }
    }
    
    function clearConflictMessages() {
        const conflictMessages = document.querySelectorAll('.alert-warning');
        conflictMessages.forEach(message => message.remove());
        
        // Enable the submit button
        const forms = document.querySelectorAll('#scheduleForm, #rescheduleForm, #bookingForm');
        forms.forEach(form => {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.classList.remove('disabled');
            }
        });
    }
    
    // Helper functions to get existing bookings and demos
    // In a real app, these would make AJAX calls to the server
    
    function getExistingBookings() {
        // This would normally be fetched from the server
        return [
            {
                id: 1,
                student_name: 'John Doe',
                start_time: '2023-11-20T10:00:00',
                end_time: '2023-11-20T11:00:00'
            },
            {
                id: 2,
                student_name: 'Jane Smith',
                start_time: '2023-11-20T14:00:00',
                end_time: '2023-11-20T15:30:00'
            }
        ];
    }
    
    function getExistingDemos() {
        // This would normally be fetched from the server
        return [
            {
                id: 1,
                student_name: 'Alice Johnson',
                start_time: '2023-11-21T09:00:00',
                end_time: '2023-11-21T10:00:00'
            },
            {
                id: 2,
                student_name: 'Bob Williams',
                start_time: '2023-11-21T11:00:00',
                end_time: '2023-11-21T12:00:00'
            }
        ];
    }
});

// CSS for conflict detection styling
const conflictDetectionStyles = `
    .alert-warning {
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;

// Add the styles to the document
const conflictDetectionStyleSheet = document.createElement('style');
conflictDetectionStyleSheet.textContent = conflictDetectionStyles;
document.head.appendChild(conflictDetectionStyleSheet);