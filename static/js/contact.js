document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('contactForm');
    const thankYou = document.getElementById('thankYouMessage');

    if (!form) return; // Sicherheitshalber abbrechen, falls kein Formular da ist

    // ===============================
    // GERÄTEÜBERGREIFENDE PARALLAX
    // ===============================
    let targetX = 0, targetY = 0;
    let currentX = 0, currentY = 0;
    let scrollOffset = 0;

    // Desktop Mausbewegung
    document.addEventListener("mousemove", (e) => {
        targetX = (e.clientX / window.innerWidth - 0.5) * 15; 
        targetY = (e.clientY / window.innerHeight - 0.5) * 15;
    });

    // Scroll-Offset
    window.addEventListener("scroll", () => {
        scrollOffset = window.scrollY * 0.05;
    });

    // Animation Loop
    function animateBackground() {
        currentX += (targetX - currentX) * 0.1;
        currentY += (targetY - currentY) * 0.1;

        // Nutzt die ID des Formulars aus dem Template
        form.style.backgroundPosition = 
            `calc(50% + ${currentX}px) calc(50% + ${currentY + scrollOffset}px)`;

        requestAnimationFrame(animateBackground);
    }

    animateBackground();
});