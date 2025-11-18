// Drag and Drop Rescheduling Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the bookings or demos page
    const bookingItems = document.querySelectorAll('.booking-item');
    const demoItems = document.querySelectorAll('.demo-item');
    const calendarGrid = document.querySelector('.calendar-grid');
    
    if (bookingItems.length > 0 || demoItems.length > 0) {
        initializeDragAndDrop();
    }
    
    function initializeDragAndDrop() {
        // Make booking and demo items draggable
        document.querySelectorAll('.booking-item, .demo-item').forEach(item => {
            item.draggable = true;
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
        });
        
        // Make calendar days drop targets
        document.querySelectorAll('.calendar-day').forEach(day => {
            day.addEventListener('dragover', handleDragOver);
            day.addEventListener('drop', handleDrop);
            day.addEventListener('dragleave', handleDragLeave);
        });
    }
    
    let draggedItem = null;
    let draggedItemType = null;
    let draggedItemId = null;
    
    function handleDragStart(e) {
        draggedItem = this;
        draggedItemType = this.classList.contains('booking-item') ? 'booking' : 'demo';
        draggedItemId = this.getAttribute('data-id');
        
        // Visual feedback
        this.style.opacity = '0.5';
        
        // Store the original position
        this.dataset.originalPosition = this.parentElement.dataset.position;
        
        // Set the drag image
        const dragImage = new Image();
        dragImage.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        e.dataTransfer.setDragImage(dragImage, 0, 0);
        
        // Set the data to be transferred
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedItemId);
        e.dataTransfer.setData('itemType', draggedItemType);
    }
    
    function handleDragEnd(e) {
        // Reset the opacity
        this.style.opacity = '1';
        
        // Reset all drop targets
        document.querySelectorAll('.calendar-day').forEach(day => {
            day.classList.remove('drag-over');
            day.classList.remove('drag-valid');
            day.classList.remove('drag-invalid');
        });
    }
    
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault(); // Necessary to allow dropping
        }
        
        e.dataTransfer.dropEffect = 'move';
        
        // Add visual feedback
        this.classList.add('drag-over');
        
        return false;
    }
    
    function handleDragLeave(e) {
        this.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation(); // Stops some browsers from redirecting
        }
        
        e.preventDefault();
        
        // Remove visual feedback
        this.classList.remove('drag-over');
        
        const dropTarget = this;
        const dropDate = dropTarget.getAttribute('data-date');
        
        if (!dropDate) {
            return false;
        }
        
        // Check if the drop target is valid
        if (isValidDropTarget(dropTarget, draggedItemType)) {
            dropTarget.classList.add('drag-valid');
            
            // Ask for confirmation
            const confirmationMessage = getConfirmationMessage(draggedItemType, draggedItemId, dropDate);
            
            if (confirm(confirmationMessage)) {
                // Perform the rescheduling
                rescheduleItem(draggedItemType, draggedItemId, dropDate);
            }
        } else {
            dropTarget.classList.add('drag-invalid');
            setTimeout(() => {
                dropTarget.classList.remove('drag-invalid');
            }, 1000);
        }
        
        return false;
    }
    
    function isValidDropTarget(dropTarget, itemType) {
        // Check if the day is not in the past
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const dropDate = new Date(dropTarget.getAttribute('data-date'));
        
        if (dropDate < today) {
            return false;
        }
        
        // Check if there's already an item at this time slot
        const existingItems = dropTarget.querySelectorAll('.booking-item, .demo-item');
        
        if (existingItems.length > 0) {
            // For now, we'll allow overlapping items but show a warning
            // In a real app, you might want to prevent this
            return true;
        }
        
        return true;
    }
    
    function getConfirmationMessage(itemType, itemId, dropDate) {
        const date = new Date(dropDate);
        const formattedDate = date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        if (itemType === 'booking') {
            return `Are you sure you want to reschedule this booking to ${formattedDate}?`;
        } else if (itemType === 'demo') {
            return `Are you sure you want to reschedule this demo to ${formattedDate}?`;
        }
        
        return `Are you sure you want to reschedule this item to ${formattedDate}?`;
    }
    
    function rescheduleItem(itemType, itemId, newDate) {
        // In a real app, this would make an AJAX call to the server
        // For now, we'll just show a success message
        
        const url = itemType === 'booking' 
            ? `/tutor/reschedule-booking/${itemId}` 
            : `/tutor/reschedule-demo/${itemId}`;
        
        const formData = new FormData();
        formData.append('new_date', newDate);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                showSuccessMessage(itemType, data.message);
                
                // Update the UI
                updateCalendarUI(itemType, itemId, newDate);
            } else {
                // Show error message
                showErrorMessage(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('An error occurred while rescheduling. Please try again.');
        });
    }
    
    function showSuccessMessage(itemType, message) {
        // Create and show a success toast
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed top-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-success text-white">
                <strong class="me-auto">Success</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    function showErrorMessage(message) {
        // Create and show an error toast
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed top-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-danger text-white">
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    function updateCalendarUI(itemType, itemId, newDate) {
        // Find the item in the calendar and update its position
        const item = document.querySelector(`[data-id="${itemId}"]`);
        
        if (item) {
            // Find the target day
            const targetDay = document.querySelector(`[data-date="${newDate}"]`);
            
            if (targetDay) {
                // Move the item to the new day
                targetDay.appendChild(item);
                
                // Update the item's time display if needed
                updateItemTimeDisplay(item, newDate);
            }
        }
    }
    
    function updateItemTimeDisplay(item, newDate) {
        // In a real app, this would update the time display based on the new date
        // For now, we'll just add a visual indicator
        const timeDisplay = item.querySelector('.time-display');
        
        if (timeDisplay) {
            const date = new Date(newDate);
            const formattedDate = date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
            });
            
            timeDisplay.textContent = `${formattedDate} - ${timeDisplay.getAttribute('data-original-time') || 'TBD'}`;
        }
    }
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// CSS for drag and drop styling
const dragDropStyles = `
    .booking-item, .demo-item {
        cursor: move;
        transition: transform 0.2s ease;
    }
    
    .booking-item:hover, .demo-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .booking-item.dragging, .demo-item.dragging {
        opacity: 0.5;
        cursor: grabbing;
    }
    
    .calendar-day {
        position: relative;
        min-height: 100px;
    }
    
    .calendar-day.drag-over {
        background-color: #e7f3ff;
        border: 2px dashed #667eea;
    }
    
    .calendar-day.drag-valid {
        background-color: #d4edda;
        border: 2px dashed #28a745;
    }
    
    .calendar-day.drag-invalid {
        background-color: #f8d7da;
        border: 2px dashed #dc3545;
    }
    
    .toast {
        min-width: 250px;
    }
`;

// Add the styles to the document
const styleSheet = document.createElement('style');
styleSheet.textContent = dragDropStyles;
document.head.appendChild(styleSheet);