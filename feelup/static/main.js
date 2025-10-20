// ===============================
// Smooth Scroll for Anchor Links
// ===============================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ===============================
// Enhanced Emoji Reaction Animation
// ===============================
function reactEmoji(button, emoji) {
    let countSpan = button.querySelector('.count');
    let count = parseInt(countSpan.textContent) || 0;
    count++;
    countSpan.textContent = count;

    // Add celebration animation
    button.classList.add('reaction-animate');
    
    // Create floating emoji effect
    const floatingEmoji = document.createElement('span');
    floatingEmoji.textContent = emoji;
    floatingEmoji.style.position = 'absolute';
    floatingEmoji.style.fontSize = '1.5rem';
    floatingEmoji.style.pointerEvents = 'none';
    floatingEmoji.style.animation = 'floatUp 1s ease-out';
    button.style.position = 'relative';
    button.appendChild(floatingEmoji);
    
    setTimeout(() => {
        button.classList.remove('reaction-animate');
        floatingEmoji.remove();
    }, 1000);
}

// Add floating animation CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes floatUp {
        0% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
        100% {
            opacity: 0;
            transform: translateY(-50px) scale(1.5);
        }
    }
`;
document.head.appendChild(style);

// ===============================
// Mobile nav toggle with animation
// ===============================
const navToggle = document.querySelector('.nav-toggle');
const navCenter = document.querySelector('.nav-center');
if (navToggle && navCenter) {
    navToggle.addEventListener('click', () => {
        const isOpen = navCenter.classList.toggle('mobile-open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        navToggle.innerHTML = isOpen ? '✕' : '☰';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navToggle.contains(e.target) && !navCenter.contains(e.target)) {
            navCenter.classList.remove('mobile-open');
            navToggle.setAttribute('aria-expanded', 'false');
            navToggle.innerHTML = '☰';
        }
    });
}

// ===============================
// Form Validation Enhancement
// ===============================
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = '#ef4444';
                field.style.animation = 'shake 0.5s';
            } else {
                field.style.borderColor = '#10b981';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// Add shake animation
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
`;
document.head.appendChild(shakeStyle);

// ===============================
// Auto-hide Flash Messages
// ===============================
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.animation = 'fadeOut 0.5s ease-out';
        setTimeout(() => {
            alert.remove();
        }, 500);
    }, 5000);
});

const fadeOutStyle = document.createElement('style');
fadeOutStyle.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(fadeOutStyle);

// ===============================
// Card Entrance Animation
// ===============================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'fadeInScale 0.6s ease-out';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.card').forEach(card => {
    observer.observe(card);
});

// ===============================
// Add Loading State to Buttons
// ===============================
document.querySelectorAll('button[type="submit"]').forEach(button => {
    button.addEventListener('click', function() {
        const form = this.closest('form');
        if (form && form.checkValidity()) {
            this.disabled = true;
            this.innerHTML = '<span class="loading"></span> Loading...';
            setTimeout(() => {
                this.disabled = false;
            }, 3000);
        }
    });
});

// ===============================
// Scroll to Top Button
// ===============================
const scrollTopBtn = document.createElement('button');
scrollTopBtn.innerHTML = '↑';
scrollTopBtn.className = 'scroll-top-btn';
scrollTopBtn.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    display: none;
    z-index: 1000;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
`;
document.body.appendChild(scrollTopBtn);

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
        scrollTopBtn.style.display = 'block';
    } else {
        scrollTopBtn.style.display = 'none';
    }
});

scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

scrollTopBtn.addEventListener('mouseenter', function() {
    this.style.transform = 'scale(1.1) translateY(-5px)';
    this.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.6)';
});

scrollTopBtn.addEventListener('mouseleave', function() {
    this.style.transform = 'scale(1) translateY(0)';
    this.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
});

// ===============================
// Initialize Tooltips (if Bootstrap)
// ===============================
if (typeof bootstrap !== 'undefined') {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

console.log('✨ FeelUP frontend enhanced and loaded successfully!');
