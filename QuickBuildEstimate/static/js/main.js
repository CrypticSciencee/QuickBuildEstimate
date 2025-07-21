// QuickBuild Estimate - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert && !alert.classList.contains('alert-permanent')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);

    // Form validation
    const validationForms = document.querySelectorAll('.needs-validation');
    validationForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // File size validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const maxSize = 16 * 1024 * 1024; // 16MB
                if (file.size > maxSize) {
                    alert('File size exceeds 16MB limit. Please choose a smaller file.');
                    this.value = '';
                    return;
                }

                // Update dropzone display
                const dropzone = this.closest('.dropzone');
                if (dropzone) {
                    updateDropzoneDisplay(dropzone, file);
                }
            }
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Dynamic number formatting
    const currencyElements = document.querySelectorAll('.currency');
    currencyElements.forEach(element => {
        const value = parseFloat(element.textContent.replace(/[^0-9.-]+/g, ''));
        if (!isNaN(value)) {
            element.textContent = formatCurrency(value);
        }
    });

    // Bundle toggle animations
    const bundleCards = document.querySelectorAll('.card[data-bundle]');
    bundleCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });

    // Progress bar updates
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 100);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new estimate
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newEstimateLink = document.querySelector('a[href*="index"]');
            if (newEstimateLink) {
                window.location.href = newEstimateLink.href;
            }
        }

        // Ctrl/Cmd + H for history
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            const historyLink = document.querySelector('a[href*="history"]');
            if (historyLink) {
                window.location.href = historyLink.href;
            }
        }

        // Escape key to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Real-time cost calculations (if on estimate page)
    const profitInput = document.getElementById('profit_percentage');
    const contingencyInput = document.getElementById('contingency_percentage');
    
    if (profitInput || contingencyInput) {
        [profitInput, contingencyInput].filter(Boolean).forEach(input => {
            input.addEventListener('input', debounce(function() {
                updateCostPreview();
            }, 500));
        });
    }

    // Auto-save form data
    const forms = document.querySelectorAll('form[data-autosave]');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                saveFormData(form);
            });
        });
        
        // Load saved data
        loadFormData(form);
    });
});

// Utility functions
function updateDropzoneDisplay(dropzone, file) {
    const content = dropzone.querySelector('.dropzone-content');
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    
    content.innerHTML = `
        <i data-feather="check-circle" class="dropzone-icon text-success"></i>
        <p class="mb-1 text-success">${file.name}</p>
        <small class="text-muted">${fileSize} MB</small>
    `;
    
    dropzone.classList.add('success');
    
    // Re-initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function updateCostPreview() {
    // This would update cost preview in real-time
    // Implementation depends on having access to estimate data
    console.log('Updating cost preview...');
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    const formId = form.id || 'default';
    localStorage.setItem(`formData_${formId}`, JSON.stringify(data));
}

function loadFormData(form) {
    const formId = form.id || 'default';
    const savedData = localStorage.getItem(`formData_${formId}`);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && input.type !== 'file') {
                    input.value = data[key];
                }
            });
        } catch (e) {
            console.warn('Could not load saved form data:', e);
        }
    }
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${getToastIcon(type)}" class="me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideToast(toast);
    }, 5000);
    
    // Close button functionality
    const closeBtn = toast.querySelector('.btn-close');
    closeBtn.addEventListener('click', () => hideToast(toast));
    
    // Re-initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function hideToast(toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'info': 'info',
        'warning': 'alert-triangle',
        'error': 'alert-circle',
        'danger': 'alert-circle'
    };
    return icons[type] || 'info';
}

// Export functions for use in other scripts
window.QuickBuild = {
    showToast,
    formatCurrency,
    debounce,
    updateDropzoneDisplay
};
