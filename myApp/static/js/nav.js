/**
 * Premium Navigation JavaScript
 * Handles mobile drawer, dropdowns, and accessibility features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu elements
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileProductsToggle = document.querySelector('.mobile-products-toggle');
    const mobileProductsMenu = document.querySelector('.mobile-products-menu');
    
    // Desktop dropdown elements
    const desktopDropdowns = document.querySelectorAll('[x-data]');
    
    // State management
    let isMobileMenuOpen = false;
    let isProductsMenuOpen = false;

    // Mobile menu toggle
    function toggleMobileMenu() {
        isMobileMenuOpen = !isMobileMenuOpen;
        
        if (isMobileMenuOpen) {
            mobileMenu.classList.remove('hidden');
            mobileMenuButton.setAttribute('aria-expanded', 'true');
            mobileMenuButton.innerHTML = '<i class="fas fa-times text-lg"></i>';
            
            // Add smooth slide animation
            mobileMenu.style.transform = 'translateY(-10px)';
            mobileMenu.style.opacity = '0';
            requestAnimationFrame(() => {
                mobileMenu.style.transition = 'all 0.2s ease-out';
                mobileMenu.style.transform = 'translateY(0)';
                mobileMenu.style.opacity = '1';
            });
        } else {
            // Close products menu if open
            if (isProductsMenuOpen) {
                toggleProductsMenu();
            }
            
            mobileMenu.style.transition = 'all 0.2s ease-in';
            mobileMenu.style.transform = 'translateY(-10px)';
            mobileMenu.style.opacity = '0';
            
            setTimeout(() => {
                mobileMenu.classList.add('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
                mobileMenuButton.innerHTML = '<i class="fas fa-bars text-lg"></i>';
            }, 200);
        }
    }

    // Products menu toggle (mobile)
    function toggleProductsMenu() {
        isProductsMenuOpen = !isProductsMenuOpen;
        const chevron = mobileProductsToggle.querySelector('i');
        
        if (isProductsMenuOpen) {
            mobileProductsMenu.classList.remove('hidden');
            chevron.style.transform = 'rotate(180deg)';
            mobileProductsToggle.setAttribute('aria-expanded', 'true');
        } else {
            mobileProductsMenu.classList.add('hidden');
            chevron.style.transform = 'rotate(0deg)';
            mobileProductsToggle.setAttribute('aria-expanded', 'false');
        }
    }

    // Close mobile menu when clicking outside
    function handleClickOutside(event) {
        if (isMobileMenuOpen && !mobileMenu.contains(event.target) && !mobileMenuButton.contains(event.target)) {
            toggleMobileMenu();
        }
    }

    // Handle keyboard navigation
    function handleKeyboard(event) {
        // ESC key closes mobile menu
        if (event.key === 'Escape') {
            if (isMobileMenuOpen) {
                toggleMobileMenu();
            }
        }
        
        // Enter/Space on mobile products toggle
        if ((event.key === 'Enter' || event.key === ' ') && event.target === mobileProductsToggle) {
            event.preventDefault();
            toggleProductsMenu();
        }
    }

    // Smooth scroll for anchor links
    function handleSmoothScroll(event) {
        const target = event.target.closest('a[href^="#"]');
        if (target) {
            event.preventDefault();
            const targetId = target.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    }

    // Initialize dropdowns with Alpine.js-like behavior
    function initializeDropdowns() {
        desktopDropdowns.forEach(dropdown => {
            const button = dropdown.querySelector('button');
            const menu = dropdown.querySelector('[x-show]');
            
            if (button && menu) {
                let isOpen = false;
                
                // Mouse events
                dropdown.addEventListener('mouseenter', () => {
                    isOpen = true;
                    menu.style.opacity = '1';
                    menu.style.visibility = 'visible';
                    menu.style.transform = 'translateY(0)';
                });
                
                dropdown.addEventListener('mouseleave', () => {
                    isOpen = false;
                    menu.style.opacity = '0';
                    menu.style.visibility = 'hidden';
                    menu.style.transform = 'translateY(8px)';
                });
                
                // Keyboard events
                button.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        isOpen = !isOpen;
                        
                        if (isOpen) {
                            menu.style.opacity = '1';
                            menu.style.visibility = 'visible';
                            menu.style.transform = 'translateY(0)';
                        } else {
                            menu.style.opacity = '0';
                            menu.style.visibility = 'hidden';
                            menu.style.transform = 'translateY(8px)';
                        }
                    }
                });
            }
        });
    }

    // Add focus management for accessibility
    function handleFocusManagement() {
        const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        
        // Trap focus in mobile menu when open
        if (isMobileMenuOpen) {
            const focusableContent = mobileMenu.querySelectorAll(focusableElements);
            const firstFocusable = focusableContent[0];
            const lastFocusable = focusableContent[focusableContent.length - 1];
            
            mobileMenu.addEventListener('keydown', (event) => {
                if (event.key === 'Tab') {
                    if (event.shiftKey) {
                        if (document.activeElement === firstFocusable) {
                            lastFocusable.focus();
                            event.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastFocusable) {
                            firstFocusable.focus();
                            event.preventDefault();
                        }
                    }
                }
            });
        }
    }

    // Initialize all functionality
    function initializeNavigation() {
        // Event listeners
        if (mobileMenuButton) {
            mobileMenuButton.addEventListener('click', toggleMobileMenu);
        }
        
        if (mobileProductsToggle) {
            mobileProductsToggle.addEventListener('click', toggleProductsMenu);
        }
        
        // Global event listeners
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('keydown', handleKeyboard);
        document.addEventListener('click', handleSmoothScroll);
        
        // Initialize dropdowns
        initializeDropdowns();
        
        // Set initial ARIA states
        if (mobileMenuButton) {
            mobileMenuButton.setAttribute('aria-expanded', 'false');
        }
        if (mobileProductsToggle) {
            mobileProductsToggle.setAttribute('aria-expanded', 'false');
        }
    }

    // Initialize when DOM is ready
    initializeNavigation();
    
    // Add smooth transitions to all interactive elements
    const interactiveElements = document.querySelectorAll('a, button, [role="button"]');
    interactiveElements.forEach(element => {
        element.style.transition = 'all 0.2s ease-out';
    });
    
    // Add hover effects for desktop
    if (window.innerWidth >= 768) {
        const navLinks = document.querySelectorAll('.nav-link, a[href]');
        navLinks.forEach(link => {
            link.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-1px)';
            });
            
            link.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    
    if (window.innerWidth >= 768 && mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
        mobileMenuButton.setAttribute('aria-expanded', 'false');
        mobileMenuButton.innerHTML = '<i class="fas fa-bars text-lg"></i>';
    }
});
