// Логика интерфейса. Автор: Ли Никита
// Hotel Management System - Main JavaScript

console.log('Hotel Management System by Li Nikita loaded');

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Auto-hide mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (mobileMenu && !mobileMenu.contains(event.target) && !mobileMenuBtn.contains(event.target)) {
            mobileMenu.classList.add('hidden');
        }
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});

// About Developer Modal Functions
function showAboutModal() {
    const modal = document.getElementById('aboutModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function hideAboutModal() {
    const modal = document.getElementById('aboutModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('aboutModal');
    if (modal && event.target === modal) {
        hideAboutModal();
    }
});

// Escape key to close modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideAboutModal();
    }
});

// Form validation and enhancement
function enhanceForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable after 3 seconds as fallback
                setTimeout(() => {
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });
}

// Status update with visual feedback
function updateRoomStatus(roomId, newStatus) {
    const roomCard = document.querySelector(`[data-room-id="${roomId}"]`);
    if (roomCard) {
        roomCard.classList.add('loading');
        
        // Simulate API call
        setTimeout(() => {
            roomCard.classList.remove('loading');
            showNotification('Статус номера обновлен!', 'success');
        }, 1000);
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform translate-x-full transition-transform duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-black' :
        'bg-blue-500 text-white'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Slide in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(full)';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Touch gestures for mobile
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', function(event) {
    touchStartX = event.changedTouches[0].screenX;
});

document.addEventListener('touchend', function(event) {
    touchEndX = event.changedTouches[0].screenX;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swipe left - could trigger next page or action
            console.log('Swipe left detected');
        } else {
            // Swipe right - could trigger previous page or action
            console.log('Swipe right detected');
        }
    }
}

// Real-time updates (WebSocket placeholder)
function initializeRealTimeUpdates() {
    // Placeholder for WebSocket connection
    console.log('Real-time updates initialized (placeholder)');
    
    // Simulate periodic updates
    setInterval(() => {
        // Update dashboard stats, room statuses, etc.
        updateDashboardStats();
    }, 30000); // Every 30 seconds
}

function updateDashboardStats() {
    // Check if we're on the dashboard page
    if (window.location.pathname === '/') {
        fetch('/api/dashboard_stats')
            .then(response => response.json())
            .then(data => {
                console.log('Dashboard stats updated:', data);
                // Update stats cards with animation
                updateStatsCards(data.room_stats, data.task_stats);
            })
            .catch(error => console.log('Stats update failed:', error));
    }
}

function updateStatsCards(roomStats, taskStats) {
    // Add subtle animation to indicate update
    const statsCards = document.querySelectorAll('[data-stat]');
    statsCards.forEach(card => {
        card.style.transform = 'scale(1.02)';
        setTimeout(() => {
            card.style.transform = 'scale(1)';
        }, 200);
    });
}

// Quick action functions for dashboard
function showCheckoutModal() {
    // Redirect to guests page for now
    window.location.href = '/guests';
}

function showCreateTaskModal() {
    // Redirect to tasks page for now
    window.location.href = '/tasks';
}

// Accessibility enhancements
function enhanceAccessibility() {
    // Add keyboard navigation for cards
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                card.click();
            }
        });
    });
    
    // Add ARIA labels where needed
    const buttons = document.querySelectorAll('button:not([aria-label])');
    buttons.forEach(button => {
        const icon = button.querySelector('i');
        if (icon && !button.textContent.trim()) {
            button.setAttribute('aria-label', 'Кнопка действия');
        }
    });
}

// Performance monitoring
function initializePerformanceMonitoring() {
    // Monitor page load time
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
        
        // Send to analytics (placeholder)
        if (loadTime > 3000) {
            console.warn('Page load time is slow');
        }
    });
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    enhanceForms();
    enhanceAccessibility();
    initializeRealTimeUpdates();
    initializePerformanceMonitoring();
    setupUzbekPhoneFormatting();
    
    console.log('Hotel Management System fully initialized');
});

// Uzbek phone number formatting
function setupUzbekPhoneFormatting() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Remove country code if entered
            if (value.startsWith('998')) {
                value = value.substring(3);
            }
            
            // Format as +998 (XX) XXX-XX-XX
            if (value.length >= 2) {
                value = value.substring(0, 9); // Limit to 9 digits
                let formatted = '+998 ';
                
                if (value.length >= 2) {
                    formatted += `(${value.substring(0, 2)})`;
                }
                if (value.length >= 3) {
                    formatted += ` ${value.substring(2, 5)}`;
                }
                if (value.length >= 6) {
                    formatted += `-${value.substring(5, 7)}`;
                }
                if (value.length >= 8) {
                    formatted += `-${value.substring(7, 9)}`;
                }
                
                e.target.value = formatted;
            } else if (value.length === 0) {
                e.target.value = '';
            } else {
                e.target.value = `+998 (${value}`;
            }
        });
        
        // Set placeholder for Uzbek format
        if (input.placeholder.includes('+7')) {
            input.placeholder = '+998 (90) 123-45-67';
        }
    });
}

// Currency formatting for Uzbek Som
function formatUzbekCurrency(amount) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount).replace('UZS', 'сум');
}

// Service Worker registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed');
            });
    });
}