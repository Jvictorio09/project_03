/**
 * Modal system with HTMX integration and accessibility
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    initModals();
    
    // Initialize tooltips for disabled buttons
    initTooltips();
});

function initModals() {
    // Handle modal triggers
    document.addEventListener('click', function(e) {
        const trigger = e.target.closest('[data-modal-target]');
        if (trigger) {
            e.preventDefault();
            const modalId = trigger.getAttribute('data-modal-target');
            const modal = document.querySelector(modalId);
            if (modal) {
                openModal(modal);
            }
        }
        
        // Handle close buttons
        const closeBtn = e.target.closest('[data-modal-close]');
        if (closeBtn) {
            e.preventDefault();
            const modal = closeBtn.closest('.modal');
            if (modal) {
                closeModal(modal);
            }
        }
    });
    
    // Handle overlay clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target);
        }
    });
    
    // Handle ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                closeModal(openModal);
            }
        }
    });
}

function openModal(modal) {
    // Show modal
    modal.classList.add('show');
    modal.style.display = 'block';
    document.body.classList.add('modal-open');
    
    // Focus management
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusableElements.length > 0) {
        focusableElements[0].focus();
    }
    
    // Trap focus
    trapFocus(modal);
}

function closeModal(modal) {
    // Hide modal
    modal.classList.remove('show');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    
    // Remove focus trap
    removeFocusTrap(modal);
}

function trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
    });
}

function removeFocusTrap(modal) {
    // Remove event listeners by cloning the modal
    const newModal = modal.cloneNode(true);
    modal.parentNode.replaceChild(newModal, modal);
}

function initTooltips() {
    // Initialize Bootstrap tooltips for disabled buttons
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// HTMX integration
document.addEventListener('htmx:beforeRequest', function(e) {
    // Show loading state for modal content
    const modal = e.target.closest('.modal');
    if (modal) {
        const modalBody = modal.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = '<div class="text-center p-4"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        }
    }
});

document.addEventListener('htmx:afterRequest', function(e) {
    // Handle modal responses
    if (e.detail.xhr.status === 200) {
        // Success - content is already loaded
    } else if (e.detail.xhr.status === 400) {
        // Validation errors - show in modal
        const modal = e.target.closest('.modal');
        if (modal) {
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = '<div class="alert alert-danger">Please check your input and try again.</div>';
            }
        }
    }
});
