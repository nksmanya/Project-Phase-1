// ===============================
// Smooth Scroll for Anchor Links
// ===============================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
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
