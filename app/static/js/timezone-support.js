// Time Zone Support
document.addEventListener('DOMContentLoaded', function() {
    // Initialize timezone support
    initializeTimezoneSupport();
    
    function initializeTimezoneSupport() {
        // Get user's timezone
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        
        // Store timezone in localStorage
        localStorage.setItem('user_timezone', userTimezone);
        
        // Add timezone selector to forms if not present
        addTimezoneSelector();
        
        // Convert all displayed times to user's timezone
        convertDisplayedTimes(userTimezone);
        
        // Add timezone info to dashboard
        addTimezoneInfo(userTimezone);
    }
    
    function addTimezoneSelector() {
        // Find forms that might need timezone selection
        const forms = document.querySelectorAll('#scheduleForm, #rescheduleForm, #availabilityForm, #profileForm');
        
        forms.forEach(form => {
            // Check if timezone selector already exists
            if (form.querySelector('#timezone_selector')) {
                return;
            }
            
            // Create timezone selector
            const timezoneDiv = document.createElement('div');
            timezoneDiv.className = 'form-group mb-3';
            timezoneDiv.innerHTML = `
                <label class="form-label" for="timezone_selector">Time Zone</label>
                <select class="form-select" id="timezone_selector">
                    <option value="UTC">UTC</option>
                    <option value="US/Eastern">US Eastern</option>
                    <option value="US/Central">US Central</option>
                    <option value="US/Mountain">US Mountain</option>
                    <option value="US/Pacific">US Pacific</option>
                    <option value="Europe/London">Europe London</option>
                    <option value="Europe/Paris">Europe Paris</option>
                    <option value="Asia/Calcutta">Asia Calcutta</option>
                    <option value="Asia/Shanghai">Asia Shanghai</option>
                    <option value="Asia/Tokyo">Asia Tokyo</option>
                    <option value="Australia/Sydney">Australia Sydney</option>
                </select>
                <small class="form-text">Select your timezone for accurate scheduling</small>
            `;
            
            // Insert before the submit button
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                form.insertBefore(timezoneDiv, submitButton);
            } else {
                form.appendChild(timezoneDiv);
            }
            
            // Set current timezone as selected
            const userTimezone = localStorage.getItem('user_timezone');
            if (userTimezone) {
                timezoneDiv.querySelector('#timezone_selector').value = userTimezone;
            }
            
            // Add change event listener
            timezoneDiv.querySelector('#timezone_selector').addEventListener('change', function() {
                localStorage.setItem('user_timezone', this.value);
                convertDisplayedTimes(this.value);
            });
        });
    }
    
    function convertDisplayedTimes(timezone) {
        // Find all time elements
        const timeElements = document.querySelectorAll('[data-utc-time]');
        
        timeElements.forEach(element => {
            const utcTime = element.getAttribute('data-utc-time');
            if (utcTime) {
                const date = new Date(utcTime);
                const localTime = convertToTimezone(date, timezone);
                
                // Update element with local time
                element.textContent = localTime;
                
                // Add timezone indicator
                if (!element.querySelector('.timezone-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'timezone-indicator badge bg-secondary ms-1';
                    indicator.textContent = getTimezoneAbbreviation(timezone);
                    element.appendChild(indicator);
                }
            }
        });
        
        // Convert datetime elements
        const datetimeElements = document.querySelectorAll('[data-utc-datetime]');
        
        datetimeElements.forEach(element => {
            const utcDatetime = element.getAttribute('data-utc-datetime');
            if (utcDatetime) {
                const date = new Date(utcDatetime);
                const localDatetime = convertToTimezone(date, timezone, true);
                
                // Update element with local datetime
                element.textContent = localDatetime;
                
                // Add timezone indicator
                if (!element.querySelector('.timezone-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'timezone-indicator badge bg-secondary ms-1';
                    indicator.textContent = getTimezoneAbbreviation(timezone);
                    element.appendChild(indicator);
                }
            }
        });
    }
    
    function convertToTimezone(date, timezone, includeDate = false) {
        try {
            const options = {
                timeZone: timezone,
                hour: '2-digit',
                minute: '2-digit'
            };
            
            if (includeDate) {
                options.year = 'numeric';
                options.month = 'short';
                options.day = 'numeric';
            }
            
            return date.toLocaleString('en-US', options);
        } catch (e) {
            console.error('Timezone conversion error:', e);
            return date.toLocaleString();
        }
    }
    
    function getTimezoneAbbreviation(timezone) {
        const abbreviations = {
            'UTC': 'UTC',
            'US/Eastern': 'ET',
            'US/Central': 'CT',
            'US/Mountain': 'MT',
            'US/Pacific': 'PT',
            'Europe/London': 'GMT',
            'Europe/Paris': 'CET',
            'Asia/Calcutta': 'IST',
            'Asia/Shanghai': 'CST',
            'Asia/Tokyo': 'JST',
            'Australia/Sydney': 'AEST'
        };
        
        return abbreviations[timezone] || timezone;
    }
    
    function addTimezoneInfo(timezone) {
        // Find dashboard or main content area
        const dashboard = document.querySelector('.dashboard') || 
                       document.querySelector('.main-content') ||
                       document.querySelector('.container');
        
        if (dashboard) {
            // Check if timezone info already exists
            if (dashboard.querySelector('.timezone-info')) {
                return;
            }
            
            // Create timezone info element
            const timezoneInfo = document.createElement('div');
            timezoneInfo.className = 'timezone-info alert alert-info alert-dismissible fade show mb-3';
            timezoneInfo.setAttribute('role', 'alert');
            timezoneInfo.innerHTML = `
                <i class="fas fa-globe me-2"></i>
                <strong>Time Zone:</strong> ${timezone} (${getTimezoneAbbreviation(timezone)})
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            // Insert at the top of the dashboard
            dashboard.insertBefore(timezoneInfo, dashboard.firstChild);
        }
    }
    
    // Function to get timezone offset for calculations
    function getTimezoneOffset(timezone) {
        try {
            const date = new Date();
            const utcDate = new Date(date.toLocaleString('en-US', { timeZone: 'UTC' }));
            const localDate = new Date(date.toLocaleString('en-US', { timeZone: timezone }));
            
            return (localDate - utcDate) / (1000 * 60 * 60); // Return offset in hours
        } catch (e) {
            console.error('Error getting timezone offset:', e);
            return 0;
        }
    }
    
    // Function to convert time from one timezone to another
    function convertTimeBetweenTimezones(time, fromTimezone, toTimezone) {
        try {
            // Create a date object with the original time
            const date = new Date(time);
            
            // Format the time in the source timezone
            const sourceTime = date.toLocaleString('en-US', { timeZone: fromTimezone });
            
            // Create a new date object from the source time
            const sourceDate = new Date(sourceTime);
            
            // Get the offset difference between timezones
            const fromOffset = getTimezoneOffset(fromTimezone);
            const toOffset = getTimezoneOffset(toTimezone);
            const offsetDiff = toOffset - fromOffset;
            
            // Apply the offset difference
            const convertedDate = new Date(sourceDate.getTime() + offsetDiff * 60 * 60 * 1000);
            
            return convertedDate;
        } catch (e) {
            console.error('Error converting time between timezones:', e);
            return new Date(time);
        }
    }
    
    // Make functions available globally
    window.TimezoneSupport = {
        convertToTimezone,
        convertTimeBetweenTimezones,
        getTimezoneOffset,
        getTimezoneAbbreviation
    };
});

// CSS for timezone support styling
const timezoneStyles = `
    .timezone-indicator {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
    }
    
    .timezone-info {
        font-size: 0.9rem;
    }
    
    .form-group {
        margin-bottom: 1rem;
    }
    
    .form-label {
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .form-text {
        font-size: 0.875rem;
        color: #6c757d;
    }
`;

// Add styles to document
const timezoneStyleSheet = document.createElement('style');
timezoneStyleSheet.textContent = timezoneStyles;
document.head.appendChild(timezoneStyleSheet);