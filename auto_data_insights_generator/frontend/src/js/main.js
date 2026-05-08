/**
 * Auto Data Insights Generator - Enhanced Frontend JavaScript
 * Handles: navigation, drag-and-drop, alerts, scroll animations,
 * 3D card tilt effects, and button ripple effects.
 */

document.addEventListener('DOMContentLoaded', () => {
    initNavToggle();
    initDropZone();
    initAlertAutoDismiss();
    initScrollAnimations();
    init3DTiltEffect();
    initButtonRipple();
});

/* ================================================
   Navigation Toggle (Mobile)
   ================================================ */
function initNavToggle() {
    const toggle = document.getElementById('nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (toggle && navLinks) {
        toggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            toggle.classList.toggle('active');
        });

        // Close menu when clicking a link
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                toggle.classList.remove('active');
            });
        });
    }
}

/* ================================================
   Drag & Drop Upload Zone
   ================================================ */
function initDropZone() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('dataset-file');
    const nameField = document.getElementById('name');

    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateDropZoneUI(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            updateDropZoneUI(fileInput.files[0]);
        }
    });

    function updateDropZoneUI(file) {
        const content = dropZone.querySelector('.drop-zone-content');
        const ext = file.name.split('.').pop().toUpperCase();
        const size = formatFileSize(file.size);

        content.innerHTML = `
            <div class="drop-icon">✅</div>
            <h3>${file.name}</h3>
            <p>${ext} file • ${size}</p>
            <p class="drop-subtitle">Click "Upload & Process" to continue</p>
        `;

        // Auto-fill name field if empty
        if (nameField && !nameField.value) {
            nameField.value = file.name.replace(/\.[^.]+$/, '');
        }
    }
}

/* ================================================
   Alert Auto-Dismiss
   ================================================ */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('[data-auto-dismiss]');
    alerts.forEach(alert => {
        const delay = parseInt(alert.dataset.autoDismiss) || 5000;
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(30px)';
            setTimeout(() => alert.remove(), 300);
        }, delay);
    });
}

/* ================================================
   Scroll Reveal Animations
   ================================================ */
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.feature-card, .workflow-step, .dataset-card, .insight-card, .stat-card, .chart-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(25px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

/* ================================================
   3D Tilt Effect on Cards (mouse tracking)
   ================================================ */
function init3DTiltEffect() {
    const cards = document.querySelectorAll('.feature-card, .dataset-card, .insight-card, .stat-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -4; // max 4deg
            const rotateY = ((x - centerX) / centerX) * 4;  // max 4deg

            card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(800px) rotateX(0) rotateY(0) translateY(0)';
            card.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        });

        card.addEventListener('mouseenter', () => {
            card.style.transition = 'transform 0.1s ease';
        });
    });
}

/* ================================================
   Button Ripple Effect
   ================================================ */
function initButtonRipple() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('btn-ripple');

            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

/* ================================================
   Utility Functions
   ================================================ */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}
