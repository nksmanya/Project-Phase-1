// ===============================
// Smooth Scroll for Anchor Links
// ===============================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// ===============================
// Simple Emoji Reaction Animation
// ===============================
function reactEmoji(button, emoji) {
    let countSpan = button.querySelector('.count');
    let count = parseInt(countSpan.textContent) || 0;
    count++;
    countSpan.textContent = count;

    button.classList.add('reaction-animate');
    setTimeout(() => {
        button.classList.remove('reaction-animate');
    }, 500);
}

// ===============================
// Mobile nav toggle
// ===============================
const navToggle = document.querySelector('.nav-toggle');
const navCenter = document.querySelector('.nav-center');
if (navToggle && navCenter) {
    navToggle.addEventListener('click', () => {
        const isOpen = navCenter.classList.toggle('mobile-open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
}
