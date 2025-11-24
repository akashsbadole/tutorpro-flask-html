// PWA Installation and Management Script
let deferredPrompt;
let installButton;

// Initialize PWA installation
function initPWAInstall() {
  installButton = document.getElementById('pwa-install-button');
  
  // Check if app is running in standalone mode
  if (isPWAInstalled()) {
    hideInstallButton();
  } else {
    showInstallButton();
  }
  
  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    showInstallButton();
  });
}

// Check if PWA is already installed
function isPWAInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true ||
         document.referrer.includes('android-app://');
}

// Show install button
function showInstallButton() {
  if (installButton) {
    installButton.style.display = 'block';
    installButton.addEventListener('click', installPWA);
  }
}

// Hide install button
function hideInstallButton() {
  if (installButton) {
    installButton.style.display = 'none';
  }
}

// Install PWA
function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((result) => {
      if (result.outcome === 'accepted') {
        console.log('PWA installed successfully');
        hideInstallButton();
        
        // Track installation analytics
        if (typeof gtag !== 'undefined') {
          gtag('event', 'pwa_install', {
            'event_category': 'PWA',
            'event_label': 'install_success',
            'value': 1
          });
        }
        
        // Show success message
        showInstallMessage('PWA installed successfully! You can now access TutorPro from your home screen.');
      } else if (result.outcome === 'dismissed') {
        console.log('PWA installation dismissed');
        // Track dismissal analytics
        if (typeof gtag !== 'undefined') {
          gtag('event', 'pwa_install', {
            'event_category': 'PWA',
            'event_label': 'install_dismissed',
            'value': 1
          });
        }
      }
    });
    
    deferredPrompt = null;
  }
}

// Show installation message
function showInstallMessage(message) {
  // Create or update message element
  let messageDiv = document.getElementById('pwa-install-message');
  if (!messageDiv) {
    messageDiv = document.createElement('div');
    messageDiv.id = 'pwa-install-message';
    messageDiv.className = 'alert alert-success alert-dismissible fade show';
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '9999';
    messageDiv.innerHTML = `
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button>
      ${message}
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (messageDiv) {
        messageDiv.remove();
      }
    }, 5000);
  }
  
  // Add close button functionality
  document.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('close')) {
      const messageDiv = document.getElementById('pwa-install-message');
      if (messageDiv) {
        messageDiv.remove();
      }
    }
  });
}

// Check for PWA updates
function checkForPWAUpdate() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (navigator.serviceWorker.controller) {
        console.log('PWA updated');
        showUpdateMessage('A new version of TutorPro is available. Please refresh the page.');
      }
    });
  }
}

// Show update message
function showUpdateMessage(message) {
  let messageDiv = document.getElementById('pwa-update-message');
  if (!messageDiv) {
    messageDiv = document.createElement('div');
    messageDiv.id = 'pwa-update-message';
    messageDiv.className = 'alert alert-info alert-dismissible fade show';
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '9999';
    messageDiv.innerHTML = `
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button>
      <strong>Update Available:</strong> ${message}
      <button type="button" class="btn btn-primary" onclick="location.reload()">Refresh Now</button>
    `;
    
    document.body.appendChild(messageDiv);
  }
  
  // Add close button functionality
  document.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('close')) {
      const messageDiv = document.getElementById('pwa-update-message');
      if (messageDiv) {
        messageDiv.remove();
      }
    }
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initPWAInstall();
  checkForPWAUpdate();
});