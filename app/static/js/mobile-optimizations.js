// Mobile Optimizations and Touch Interactions for TutorPro
class MobileOptimizer {
    constructor() {
        this.isMobile = this.detectMobileDevice();
        this.touchStartY = 0;
        this.touchEndY = 0;
        this.isPulling = false;
        this.pullThreshold = 100;
        
        this.init();
    }

    detectMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    init() {
        if (!this.isMobile) return;

        this.setupTouchInteractions();
        this.setupPullToRefresh();
        this.setupSwipeGestures();
        this.setupVirtualKeyboardHandling();
        this.setupMobileNavigation();
        this.setupPerformanceOptimizations();
        this.setupAccessibilityEnhancements();
    }

    setupTouchInteractions() {
        // Add touch feedback to interactive elements
        const touchElements = document.querySelectorAll('.btn, .nav-link, .card, .tutor-card');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', (e) => {
                element.style.transform = 'scale(0.98)';
                element.style.transition = 'transform 0.1s ease';
            }, { passive: true });

            element.addEventListener('touchend', (e) => {
                element.style.transform = 'scale(1)';
            }, { passive: true });

            element.addEventListener('touchcancel', (e) => {
                element.style.transform = 'scale(1)';
            }, { passive: true });
        });

        // Prevent double-tap zoom on buttons
        document.addEventListener('touchend', (e) => {
            if (e.target.closest('.btn, .nav-link')) {
                e.preventDefault();
                e.target.click();
            }
        }, { passive: false });
    }

    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let pulling = false;
        const pullIndicator = document.createElement('div');
        pullIndicator.className = 'pull-to-refresh';
        pullIndicator.innerHTML = '<i class="fas fa-sync-alt"></i> Pull to refresh';
        document.body.appendChild(pullIndicator);

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                pulling = true;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!pulling) return;
            
            currentY = e.touches[0].clientY;
            const pullDistance = currentY - startY;
            
            if (pullDistance > 0 && pullDistance < 200) {
                e.preventDefault();
                pullIndicator.style.transform = `translateY(${pullDistance}px)`;
                pullIndicator.classList.toggle('active', pullDistance > this.pullThreshold);
            }
        }, { passive: false });

        document.addEventListener('touchend', () => {
            if (!pulling) return;
            
            const pullDistance = currentY - startY;
            pullIndicator.style.transform = 'translateY(0)';
            
            if (pullDistance > this.pullThreshold) {
                this.triggerRefresh();
            }
            
            pulling = false;
        }, { passive: true });
    }

    setupSwipeGestures() {
        const swipeableElements = document.querySelectorAll('.swipe-container');
        
        swipeableElements.forEach(container => {
            let startX = 0;
            let currentX = 0;
            let swiping = false;

            container.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
                swiping = true;
            }, { passive: true });

            container.addEventListener('touchmove', (e) => {
                if (!swiping) return;
                
                currentX = e.touches[0].clientX;
                const deltaX = currentX - startX;
                const swipeItem = container.querySelector('.swipe-item');
                
                if (deltaX < -50) {
                    swipeItem.style.transform = `translateX(${deltaX}px)`;
                }
            }, { passive: true });

            container.addEventListener('touchend', () => {
                if (!swiping) return;
                
                const deltaX = currentX - startX;
                const swipeItem = container.querySelector('.swipe-item');
                
                if (deltaX < -100) {
                    swipeItem.classList.add('swiped-left');
                    this.onSwipeAction(container);
                } else {
                    swipeItem.style.transform = 'translateX(0)';
                }
                
                swiping = false;
            }, { passive: true });
        });
    }

    setupVirtualKeyboardHandling() {
        // Handle virtual keyboard appearance/disappearance
        let initialViewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
        
        const handleViewportChange = () => {
            const currentHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
            const heightDifference = initialViewportHeight - currentHeight;
            
            if (heightDifference > 150) {
                // Keyboard is likely visible
                document.body.classList.add('keyboard-visible');
                this.adjustForKeyboard();
            } else {
                // Keyboard is likely hidden
                document.body.classList.remove('keyboard-visible');
                this.resetAfterKeyboard();
            }
        };

        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', handleViewportChange);
        } else {
            window.addEventListener('resize', handleViewportChange);
        }

        // Handle input focus events
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                setTimeout(() => {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            });
        });
    }

    setupMobileNavigation() {
        // Create mobile bottom navigation if it doesn't exist
        if (!document.querySelector('.mobile-bottom-nav')) {
            this.createMobileBottomNav();
        }

        // Handle mobile menu toggle
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navbarToggler.addEventListener('click', () => {
                navbarCollapse.classList.toggle('show');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navbarToggler.contains(e.target) && !navbarCollapse.contains(e.target)) {
                    navbarCollapse.classList.remove('show');
                }
            });
        }
    }

    createMobileBottomNav() {
        const bottomNav = document.createElement('nav');
        bottomNav.className = 'mobile-bottom-nav';
        bottomNav.innerHTML = `
            <a href="/" class="mobile-bottom-nav-item ${window.location.pathname === '/' ? 'active' : ''}">
                <i class="fas fa-home"></i>
                <span>Home</span>
            </a>
            <a href="/tutors" class="mobile-bottom-nav-item ${window.location.pathname.includes('tutor') ? 'active' : ''}">
                <i class="fas fa-users"></i>
                <span>Tutors</span>
            </a>
            <a href="/courses" class="mobile-bottom-nav-item ${window.location.pathname.includes('course') ? 'active' : ''}">
                <i class="fas fa-book"></i>
                <span>Courses</span>
            </a>
            <a href="/dashboard" class="mobile-bottom-nav-item ${window.location.pathname.includes('dashboard') ? 'active' : ''}">
                <i class="fas fa-tachometer-alt"></i>
                <span>Dashboard</span>
            </a>
        `;
        
        document.body.appendChild(bottomNav);
    }

    setupPerformanceOptimizations() {
        // Lazy loading for images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));

        // Optimize scroll performance
        let ticking = false;
        const updateScrollPosition = () => {
            // Update scroll-based animations
            this.updateScrollEffects();
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollPosition);
                ticking = true;
            }
        }, { passive: true });

        // Reduce motion on low-end devices
        if (this.isLowEndDevice()) {
            document.body.classList.add('reduce-motion');
        }
    }

    setupAccessibilityEnhancements() {
        // Increase touch targets for better accessibility
        const touchTargets = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
        touchTargets.forEach(target => {
            const computedStyle = window.getComputedStyle(target);
            const minHeight = parseInt(computedStyle.minHeight) || parseInt(computedStyle.height);
            
            if (minHeight < 44) {
                target.style.minHeight = '44px';
                target.style.display = 'flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
        });

        // Add focus management for touch devices
        document.addEventListener('touchstart', () => {
            document.body.classList.add('touch-mode');
        });

        // Add screen reader optimizations
        const announcements = document.createElement('div');
        announcements.setAttribute('aria-live', 'polite');
        announcements.setAttribute('aria-atomic', 'true');
        announcements.className = 'sr-only';
        document.body.appendChild(announcements);

        this.announcer = announcements;
    }

    adjustForKeyboard() {
        // Adjust layout when keyboard is visible
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
            // Scroll to ensure input is visible
            setTimeout(() => {
                activeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    }

    resetAfterKeyboard() {
        // Reset layout after keyboard is hidden
        // This can be overridden by specific pages if needed
    }

    updateScrollEffects() {
        const scrolled = window.scrollY > 50;
        const navbar = document.querySelector('.navbar-modern');
        
        if (navbar) {
            navbar.classList.toggle('scrolled', scrolled);
        }
    }

    triggerRefresh() {
        const pullIndicator = document.querySelector('.pull-to-refresh');
        pullIndicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
        
        // Trigger page refresh
        setTimeout(() => {
            window.location.reload();
        }, 500);
    }

    onSwipeAction(container) {
        // Handle swipe action (e.g., delete item, show actions)
        const action = container.dataset.swipeAction;
        if (action) {
            this.announceToScreenReader(`Swiped action: ${action}`);
        }
    }

    announceToScreenReader(message) {
        if (this.announcer) {
            this.announcer.textContent = message;
            setTimeout(() => {
                this.announcer.textContent = '';
            }, 1000);
        }
    }

    isLowEndDevice() {
        // Simple detection for low-end devices
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        const isSlowConnection = connection && (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g');
        const isLowMemory = navigator.deviceMemory && navigator.deviceMemory < 2;
        const isSlowCores = navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;
        
        return isSlowConnection || isLowMemory || isSlowCores;
    }

    // Public methods
    optimizeImages() {
        // Convert images to WebP if supported
        if (this.supportsWebP()) {
            const images = document.querySelectorAll('img[src$=".jpg"], img[src$=".png"]');
            images.forEach(img => {
                const webpSrc = img.src.replace(/\.(jpg|png)$/, '.webp');
                img.src = webpSrc;
            });
        }
    }

    supportsWebP() {
        return new Promise(resolve => {
            const webP = new Image();
            webP.onload = webP.onerror = () => {
                resolve(webP.height === 2);
            };
            webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
        });
    }

    // Handle orientation changes
    setupOrientationHandling() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                // Adjust layout after orientation change
                this.adjustForOrientation();
            }, 100);
        });
    }

    adjustForOrientation() {
        const isLandscape = window.innerWidth > window.innerHeight;
        document.body.classList.toggle('landscape', isLandscape);
        document.body.classList.toggle('portrait', !isLandscape);
    }
}

// Initialize mobile optimizations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileOptimizer = new MobileOptimizer();
    
    // Make it globally available for other scripts
    window.MobileOptimizer = MobileOptimizer;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileOptimizer;
}