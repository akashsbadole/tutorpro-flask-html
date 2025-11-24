// TutorPro PWA Install and Management Script
class PWAInstallManager {
  constructor() {
    this.deferredPrompt = null;
    this.installButton = null;
    this.isInstalled = this.checkIfInstalled();
    this.isStandalone = this.checkIfStandalone();
    
    this.init();
  }

  init() {
    // Listen for beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
      this.trackInstallPrompt();
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      this.hideInstallButton();
      this.trackInstallSuccess();
      this.showInstallSuccess();
    });

    // Check if app is already installed
    if (this.isInstalled) {
      this.hideInstallButton();
    }

    // Create install button if it doesn't exist
    this.createInstallButton();
    
    // Initialize offline indicators
    this.initOfflineIndicator();
    
    // Initialize push notifications
    this.initPushNotifications();
  }

  checkIfInstalled() {
    // Check if app is running in standalone mode
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return true;
    }
    
    // Check for iOS standalone mode
    if (window.navigator.standalone === true) {
      return true;
    }
    
    return false;
  }

  checkIfStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
  }

  createInstallButton() {
    // Check if button already exists
    if (document.getElementById('pwa-install-btn')) {
      return;
    }

    const button = document.createElement('button');
    button.id = 'pwa-install-btn';
    button.className = 'pwa-install-btn';
    button.innerHTML = `
      <i class="fas fa-download"></i>
      <span>Install App</span>
    `;
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: linear-gradient(135deg, #007bff, #0056b3);
      color: white;
      border: none;
      border-radius: 50px;
      padding: 12px 20px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
      z-index: 1000;
      display: none;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
    `;

    button.addEventListener('mouseenter', () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 20px rgba(0, 123, 255, 0.4)';
    });

    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 15px rgba(0, 123, 255, 0.3)';
    });

    button.addEventListener('click', () => {
      this.installApp();
    });

    document.body.appendChild(button);
    this.installButton = button;
  }

  showInstallButton() {
    if (this.installButton && !this.isInstalled) {
      this.installButton.style.display = 'flex';
      
      // Animate button appearance
      setTimeout(() => {
        this.installButton.style.opacity = '1';
        this.installButton.style.transform = 'scale(1)';
      }, 100);
    }
  }

  hideInstallButton() {
    if (this.installButton) {
      this.installButton.style.display = 'none';
    }
  }

  async installApp() {
    if (!this.deferredPrompt) {
      console.log('Install prompt not available');
      return;
    }

    try {
      // Show the install prompt
      this.deferredPrompt.prompt();
      
      // Wait for user's response
      const { outcome } = await this.deferredPrompt.userChoice;
      console.log(`User response to install prompt: ${outcome}`);
      
      // Clear the deferred prompt
      this.deferredPrompt = null;
      
      if (outcome === 'accepted') {
        this.trackInstallAccepted();
      } else {
        this.trackInstallDismissed();
      }
      
    } catch (error) {
      console.error('Error during app installation:', error);
      this.trackInstallError(error);
    }
  }

  showInstallSuccess() {
    const notification = document.createElement('div');
    notification.className = 'pwa-install-success';
    notification.innerHTML = `
      <i class="fas fa-check-circle"></i>
      <span>TutorPro successfully installed!</span>
    `;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #28a745;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
      z-index: 1001;
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 500;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }

  initOfflineIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.innerHTML = `
      <i class="fas fa-wifi"></i>
      <span class="status-text">Online</span>
    `;
    indicator.style.cssText = `
      position: fixed;
      top: 20px;
      left: 20px;
      background: #28a745;
      color: white;
      padding: 8px 15px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      z-index: 1000;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
    `;

    document.body.appendChild(indicator);

    // Monitor online/offline status
    window.addEventListener('online', () => {
      indicator.style.background = '#28a745';
      indicator.querySelector('.status-text').textContent = 'Online';
      indicator.querySelector('i').className = 'fas fa-wifi';
    });

    window.addEventListener('offline', () => {
      indicator.style.background = '#dc3545';
      indicator.querySelector('.status-text').textContent = 'Offline';
      indicator.querySelector('i').className = 'fas fa-wifi-slash';
    });
  }

  async initPushNotifications() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.log('Push notifications not supported');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      
      // Check if we have permission
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        // Subscribe to push notifications
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY')
        });
        
        // Send subscription to server
        await this.sendSubscriptionToServer(subscription);
        
        console.log('Push notifications enabled');
      }
    } catch (error) {
      console.error('Error setting up push notifications:', error);
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  async sendSubscriptionToServer(subscription) {
    try {
      await fetch('/api/push-subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription)
      });
    } catch (error) {
      console.error('Error sending subscription to server:', error);
    }
  }

  // Analytics tracking methods
  trackInstallPrompt() {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_prompt_shown', {
        'event_category': 'PWA',
        'event_label': 'Install Prompt Shown'
      });
    }
  }

  trackInstallAccepted() {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_accepted', {
        'event_category': 'PWA',
        'event_label': 'Install Accepted'
      });
    }
  }

  trackInstallDismissed() {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_dismissed', {
        'event_category': 'PWA',
        'event_label': 'Install Dismissed'
      });
    }
  }

  trackInstallSuccess() {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_success', {
        'event_category': 'PWA',
        'event_label': 'Install Success'
      });
    }
  }

  trackInstallError(error) {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install_error', {
        'event_category': 'PWA',
        'event_label': 'Install Error',
        'value': error.message
      });
    }
  }

  // Public methods for manual control
  showInstallPrompt() {
    if (this.deferredPrompt) {
      this.showInstallButton();
    }
  }

  hideInstallPrompt() {
    this.hideInstallButton();
  }

  // Check if running as PWA
  isPWA() {
    return this.isStandalone;
  }

  // Get device info for analytics
  getDeviceInfo() {
    return {
      isPWA: this.isPWA(),
      isStandalone: this.isStandalone,
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      online: navigator.onLine,
      screenWidth: screen.width,
      screenHeight: screen.height,
      devicePixelRatio: window.devicePixelRatio
    };
  }
}

// Initialize PWA Install Manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.pwaInstallManager = new PWAInstallManager();
  
  // Make it globally available for other scripts
  window.PWAInstallManager = PWAInstallManager;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PWAInstallManager;
}