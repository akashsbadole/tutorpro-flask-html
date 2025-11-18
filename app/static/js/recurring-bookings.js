// Recurring Booking Support
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with booking scheduling
    const bookingForm = document.getElementById('bookingForm') || 
                       document.getElementById('scheduleForm');
    
    if (bookingForm) {
        initializeRecurringBookings();
    }
    
    function initializeRecurringBookings() {
        // Add recurring booking toggle to form
        addRecurringBookingToggle();
        
        // Initialize recurring booking options
        initializeRecurringOptions();
    }
    
    function addRecurringBookingToggle() {
        // Find the form
        const form = document.getElementById('bookingForm') || 
                     document.getElementById('scheduleForm');
        
        if (!form) {
            return;
        }
        
        // Check if recurring toggle already exists
        if (form.querySelector('#recurring_booking_toggle')) {
            return;
        }
        
        // Create recurring booking toggle
        const recurringDiv = document.createElement('div');
        recurringDiv.className = 'form-check mb-3';
        recurringDiv.innerHTML = `
            <input class="form-check-input" type="checkbox" id="recurring_booking_toggle">
            <label class="form-check-label" for="recurring_booking_toggle">
                <i class="fas fa-sync-alt me-2"></i>
                Make this a recurring booking
            </label>
        `;
        
        // Insert before the submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            form.insertBefore(recurringDiv, submitButton);
        } else {
            form.appendChild(recurringDiv);
        }
        
        // Add event listener
        recurringDiv.querySelector('#recurring_booking_toggle').addEventListener('change', function() {
            if (this.checked) {
                showRecurringOptions();
            } else {
                hideRecurringOptions();
            }
        });
    }
    
    function initializeRecurringOptions() {
        // Find the form
        const form = document.getElementById('bookingForm') || 
                     document.getElementById('scheduleForm');
        
        if (!form) {
            return;
        }
        
        // Create recurring options container
        const recurringOptions = document.createElement('div');
        recurringOptions.className = 'recurring-options border rounded p-3 mb-3';
        recurringOptions.id = 'recurring_options';
        recurringOptions.style.display = 'none';
        
        recurringOptions.innerHTML = `
            <h5 class="mb-3">Recurring Options</h5>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <label class="form-label" for="repeat_frequency">Repeat Frequency</label>
                    <select class="form-select" id="repeat_frequency">
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="biweekly">Bi-weekly</option>
                        <option value="monthly">Monthly</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label class="form-label" for="repeat_interval">Repeat Every</label>
                    <div class="input-group">
                        <input type="number" class="form-control" id="repeat_interval" min="1" max="99" value="1">
                        <span class="input-group-text" id="interval_text">day(s)</span>
                    </div>
                </div>
            </div>
            
            <div class="row mb-3" id="weekly_options" style="display: none;">
                <div class="col-md-12">
                    <label class="form-label">Days of Week</label>
                    <div class="btn-group" role="group">
                        <input type="checkbox" class="btn-check" id="day_monday" value="1">
                        <label class="btn btn-outline-primary" for="day_monday">Mon</label>
                        
                        <input type="checkbox" class="btn-check" id="day_tuesday" value="2">
                        <label class="btn btn-outline-primary" for="day_tuesday">Tue</label>
                        
                        <input type="checkbox" class="btn-check" id="day_wednesday" value="3">
                        <label class="btn btn-outline-primary" for="day_wednesday">Wed</label>
                        
                        <input type="checkbox" class="btn-check" id="day_thursday" value="4">
                        <label class="btn btn-outline-primary" for="day_thursday">Thu</label>
                        
                        <input type="checkbox" class="btn-check" id="day_friday" value="5">
                        <label class="btn btn-outline-primary" for="day_friday">Fri</label>
                        
                        <input type="checkbox" class="btn-check" id="day_saturday" value="6">
                        <label class="btn btn-outline-primary" for="day_saturday">Sat</label>
                        
                        <input type="checkbox" class="btn-check" id="day_sunday" value="0">
                        <label class="btn btn-outline-primary" for="day_sunday">Sun</label>
                    </div>
                </div>
            </div>
            
            <div class="row mb-3" id="monthly_options" style="display: none;">
                <div class="col-md-6">
                    <label class="form-label">Monthly Pattern</label>
                    <select class="form-select" id="monthly_pattern">
                        <option value="date">On a specific date (e.g., 15th of each month)</option>
                        <option value="day">On a specific day (e.g., 3rd Monday of each month)</option>
                    </select>
                </div>
                <div class="col-md-6" id="monthly_date_option">
                    <label class="form-label" for="monthly_date">Date</label>
                    <input type="number" class="form-control" id="monthly_date" min="1" max="31" value="1">
                </div>
                <div class="col-md-6" id="monthly_day_option" style="display: none;">
                    <label class="form-label" for="monthly_day">Day</label>
                    <select class="form-select" id="monthly_day">
                        <option value="1">First</option>
                        <option value="2">Second</option>
                        <option value="3">Third</option>
                        <option value="4">Fourth</option>
                        <option value="-1">Last</option>
                    </select>
                </div>
                <div class="col-md-6" id="monthly_weekday_option" style="display: none;">
                    <label class="form-label" for="monthly_weekday">Weekday</label>
                    <select class="form-select" id="monthly_weekday">
                        <option value="1">Monday</option>
                        <option value="2">Tuesday</option>
                        <option value="3">Wednesday</option>
                        <option value="4">Thursday</option>
                        <option value="5">Friday</option>
                        <option value="6">Saturday</option>
                        <option value="0">Sunday</option>
                    </select>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <label class="form-label" for="end_date">End Date (Optional)</label>
                    <input type="date" class="form-control" id="end_date">
                    <small class="form-text">Leave blank to continue indefinitely</small>
                </div>
                <div class="col-md-6">
                    <label class="form-label" for="end_after">End After (Optional)</label>
                    <input type="number" class="form-control" id="end_after" min="1" max="99" placeholder="Number of occurrences">
                    <small class="form-text">Leave blank to continue indefinitely</small>
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Summary</label>
                <div class="alert alert-info" id="recurring_summary">
                    Select options to see a summary of the recurring booking pattern.
                </div>
            </div>
        `;
        
        // Insert after the recurring toggle
        const recurringToggle = form.querySelector('#recurring_booking_toggle');
        if (recurringToggle) {
            form.insertBefore(recurringOptions, recurringToggle.nextSibling);
        } else {
            form.appendChild(recurringOptions);
        }
        
        // Add event listeners for recurring options
        addRecurringOptionListeners();
    }
    
    function addRecurringOptionListeners() {
        // Frequency change
        document.getElementById('repeat_frequency').addEventListener('change', updateFrequencyOptions);
        
        // Interval change
        document.getElementById('repeat_interval').addEventListener('input', updateRecurringSummary);
        
        // Weekly options
        document.querySelectorAll('#weekly_options input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', updateRecurringSummary);
        });
        
        // Monthly options
        document.getElementById('monthly_pattern').addEventListener('change', updateMonthlyOptions);
        document.getElementById('monthly_date').addEventListener('input', updateRecurringSummary);
        document.getElementById('monthly_day').addEventListener('change', updateRecurringSummary);
        document.getElementById('monthly_weekday').addEventListener('change', updateRecurringSummary);
        
        // End options
        document.getElementById('end_date').addEventListener('change', updateRecurringSummary);
        document.getElementById('end_after').addEventListener('input', updateRecurringSummary);
    }
    
    function showRecurringOptions() {
        const options = document.getElementById('recurring_options');
        if (options) {
            options.style.display = 'block';
            updateRecurringSummary();
        }
    }
    
    function hideRecurringOptions() {
        const options = document.getElementById('recurring_options');
        if (options) {
            options.style.display = 'none';
        }
    }
    
    function updateFrequencyOptions() {
        const frequency = document.getElementById('repeat_frequency').value;
        const intervalText = document.getElementById('interval_text');
        const weeklyOptions = document.getElementById('weekly_options');
        const monthlyOptions = document.getElementById('monthly_options');
        
        // Update interval text
        switch (frequency) {
            case 'daily':
                intervalText.textContent = 'day(s)';
                weeklyOptions.style.display = 'none';
                monthlyOptions.style.display = 'none';
                break;
            case 'weekly':
                intervalText.textContent = 'week(s)';
                weeklyOptions.style.display = 'block';
                monthlyOptions.style.display = 'none';
                break;
            case 'biweekly':
                intervalText.textContent = 'bi-week(s)';
                weeklyOptions.style.display = 'block';
                monthlyOptions.style.display = 'none';
                break;
            case 'monthly':
                intervalText.textContent = 'month(s)';
                weeklyOptions.style.display = 'none';
                monthlyOptions.style.display = 'block';
                break;
        }
        
        updateRecurringSummary();
    }
    
    function updateMonthlyOptions() {
        const pattern = document.getElementById('monthly_pattern').value;
        const dateOption = document.getElementById('monthly_date_option');
        const dayOption = document.getElementById('monthly_day_option');
        const weekdayOption = document.getElementById('monthly_weekday_option');
        
        if (pattern === 'date') {
            dateOption.style.display = 'block';
            dayOption.style.display = 'none';
            weekdayOption.style.display = 'none';
        } else {
            dateOption.style.display = 'none';
            dayOption.style.display = 'block';
            weekdayOption.style.display = 'block';
        }
        
        updateRecurringSummary();
    }
    
    function updateRecurringSummary() {
        const frequency = document.getElementById('repeat_frequency').value;
        const interval = document.getElementById('repeat_interval').value;
        const endDate = document.getElementById('end_date').value;
        const endAfter = document.getElementById('end_after').value;
        
        let summary = '';
        
        // Build summary based on frequency
        switch (frequency) {
            case 'daily':
                summary = `Repeats every ${interval} day(s)`;
                break;
            case 'weekly':
                const selectedDays = getSelectedWeekdays();
                if (selectedDays.length > 0) {
                    summary = `Repeats every ${interval} week(s) on ${selectedDays.join(', ')}`;
                } else {
                    summary = `Repeats every ${interval} week(s)`;
                }
                break;
            case 'biweekly':
                const selectedDaysBi = getSelectedWeekdays();
                if (selectedDaysBi.length > 0) {
                    summary = `Repeats every ${interval} bi-week(s) on ${selectedDaysBi.join(', ')}`;
                } else {
                    summary = `Repeats every ${interval} bi-week(s)`;
                }
                break;
            case 'monthly':
                const pattern = document.getElementById('monthly_pattern').value;
                if (pattern === 'date') {
                    const date = document.getElementById('monthly_date').value;
                    summary = `Repeats every ${interval} month(s) on the ${getDateWithSuffix(date)}`;
                } else {
                    const day = document.getElementById('monthly_day').value;
                    const weekday = document.getElementById('monthly_weekday').value;
                    const dayText = getDayText(day);
                    const weekdayText = getWeekdayText(weekday);
                    summary = `Repeats every ${interval} month(s) on the ${dayText} ${weekdayText}`;
                }
                break;
        }
        
        // Add end condition
        if (endDate) {
            const formattedDate = new Date(endDate).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            summary += `, ending on ${formattedDate}`;
        } else if (endAfter) {
            summary += `, ending after ${endAfter} occurrence(s)`;
        }
        
        // Update summary display
        document.getElementById('recurring_summary').textContent = summary;
    }
    
    function getSelectedWeekdays() {
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const selectedDays = [];
        
        document.querySelectorAll('#weekly_options input[type="checkbox"]:checked').forEach(checkbox => {
            const value = parseInt(checkbox.value);
            selectedDays.push(days[value]);
        });
        
        return selectedDays;
    }
    
    function getDateWithSuffix(date) {
        if (!date) return '';
        
        const suffixes = ['th', 'st', 'nd', 'rd'];
        const value = parseInt(date);
        const suffix = (value > 3 && value < 21) ? 'th' : suffixes[value % 10] || 'th';
        
        return `${date}${suffix}`;
    }
    
    function getDayText(day) {
        const dayTexts = {
            '1': 'First',
            '2': 'Second',
            '3': 'Third',
            '4': 'Fourth',
            '-1': 'Last'
        };
        
        return dayTexts[day] || '';
    }
    
    function getWeekdayText(weekday) {
        const weekdayTexts = {
            '0': 'Sunday',
            '1': 'Monday',
            '2': 'Tuesday',
            '3': 'Wednesday',
            '4': 'Thursday',
            '5': 'Friday',
            '6': 'Saturday'
        };
        
        return weekdayTexts[weekday] || '';
    }
    
    // Make functions available globally
    window.RecurringBookings = {
        showRecurringOptions,
        hideRecurringOptions,
        updateRecurringSummary
    };
});

// CSS for recurring bookings styling
const recurringStyles = `
    .recurring-options {
        background-color: #f8f9fa;
    }
    
    .recurring-options h5 {
        color: #495057;
        font-weight: 600;
    }
    
    .btn-check:checked + .btn {
        background-color: #667eea;
        border-color: #667eea;
        color: white;
    }
    
    .alert-info {
        border-radius: 0.5rem;
    }
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = recurringStyles;
document.head.appendChild(styleSheet);