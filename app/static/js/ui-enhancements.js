// Modern UI Enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Sticky Navigation
    const navbar = document.querySelector('.navbar-modern');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // Search Functionality
    const searchInput = document.querySelector('.search-input-modern');
    const searchSuggestions = document.querySelector('.search-suggestions');
    
    if (searchInput && searchSuggestions) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            if (query.length > 2) {
                // Show loading state
                searchInput.classList.add('loading-modern');
                
                // Simulate API call for suggestions
                setTimeout(() => {
                    searchInput.classList.remove('loading-modern');
                    // Show suggestions (mock data for now)
                    showSearchSuggestions(query);
                }, 500);
            } else {
                searchSuggestions.innerHTML = '';
                searchSuggestions.style.display = 'none';
            }
        });
    }
    
    // Tutor Card Interactions
    const tutorCards = document.querySelectorAll('.tutor-card');
    tutorCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Form Enhancements
    const forms = document.querySelectorAll('.form-modern');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
    });
    
    // Mobile Menu Toggle
    const mobileMenuToggle = document.querySelector('.navbar-toggler');
    const mobileMenu = document.querySelector('.navbar-collapse');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('show');
            this.classList.toggle('active');
        });
    }
    
    // Smooth Scroll for Anchor Links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy Loading for Images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // Notification System
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Global notification function
    window.showNotification = showNotification;
    
    // Progressive Enhancement for Dashboard
    function animateValue(element, start, end, duration) {
        const startTime = performance.now();
        const updateValue = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = start + (end - start) * progress;
            element.textContent = Math.floor(current);
            
            if (progress < 1) {
                requestAnimationFrame(updateValue);
            }
        };
        
        requestAnimationFrame(updateValue);
    }
    
    // Animate statistics on dashboard
    const statValues = document.querySelectorAll('.card-value-modern');
    statValues.forEach(element => {
        const finalValue = parseInt(element.textContent);
        if (finalValue > 0) {
            animateValue(element, 0, finalValue, 2000);
        }
    });
});

// Search Suggestions Function
function showSearchSuggestions(query) {
    const suggestions = [
        'Mathematics', 'English', 'Programming', 'Science', 'History',
        'Spanish', 'French', 'German', 'Physics', 'Chemistry'
    ];
    
    const filteredSuggestions = suggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5);
    
    const searchSuggestions = document.querySelector('.search-suggestions');
    if (filteredSuggestions.length > 0) {
        searchSuggestions.innerHTML = filteredSuggestions.map(suggestion =>
            `<div class="suggestion-item" onclick="selectSuggestion('${suggestion}')">
                <i class="fas fa-search"></i>
                ${suggestion}
            </div>`
        ).join('');
        searchSuggestions.style.display = 'block';
    } else {
        searchSuggestions.style.display = 'none';
    }
}

// Select Suggestion Function
function selectSuggestion(suggestion) {
    const searchInput = document.querySelector('.search-input-modern');
    searchInput.value = suggestion;
    document.querySelector('.search-suggestions').style.display = 'none';
    searchInput.focus();
}