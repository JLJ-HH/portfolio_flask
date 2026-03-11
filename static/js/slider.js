(function() {
    // =================================================
    // SLIDER INITIALISIERUNG
    // =================================================
    const slider = document.querySelector(".slider");
    if (!slider) return;

    const items = slider.querySelectorAll(".item");
    const next = document.getElementById("next");
    const prev = document.getElementById("prev");
    if (!items.length || !next || !prev) return;

    let active = Math.floor(items.length / 2); // Start: mittlere Card aktiv

    function loadShow() {
        items.forEach((item, index) => {
            item.style.transition = "transform 0.5s ease, opacity 0.5s ease, filter 0.5s ease, z-index 0.5s ease";
            
            if (index === active) {
                // AKTIVE CARD
                item.style.transform = "translate(-50%, -50%)scale(1)";
                item.style.zIndex = "1000";       
                item.style.filter = "none";       
                item.style.opacity = "1";
                item.style.pointerEvents = "auto"; 
                item.style.overflow = "visible";  
            } else {
                // INAKTIVE CARDS
                let stt = Math.abs(index - active);
                let direction = index > active ? 1 : -1;
                let offset = window.innerWidth <= 768 ? 120 : 200; 
                
                item.style.transform = `translateX(${offset * stt * direction}px) translateY(-50%) scale(${1 - 0.2 * stt}) perspective(1000px) rotateY(${direction * -1}deg)`;
                item.style.zIndex = 50 - stt;     
                item.style.filter = "blur(5px)";  
                item.style.opacity = stt > 2 ? "0" : "0.6";
                item.style.pointerEvents = "none"; 
                item.style.overflow = "hidden";   
                
                // Alle Overlays bei inaktiven Karten schließen
                item.querySelectorAll('.card-info, .card-structure').forEach(ov => ov.style.display = 'none');
            }
        });
    }

    loadShow();
    window.addEventListener("resize", loadShow);

    // =================================================
    // NAVIGATION
    // =================================================
    next.onclick = () => { if(active + 1 < items.length) { active++; loadShow(); } };
    prev.onclick = () => { if(active - 1 >= 0) { active--; loadShow(); } };

    // =================================================
    // NEUE UNIVERSELLE OVERLAY-LOGIK
    // =================================================

    window.toggleOverlay = function(btnOrElement, targetClass) {
        // Findet die Karte (item)
        const card = btnOrElement.closest('.item');
        if (!card) return;

        const targetOverlay = card.querySelector(targetClass);
        const allOverlays = card.querySelectorAll('.card-info, .card-structure');

        // 1. Andere Overlays auf DIESER Karte schließen
        allOverlays.forEach(ov => {
            if (ov !== targetOverlay) ov.style.display = 'none';
        });

        // 2. Status prüfen und toggeln
        const isOpen = targetOverlay.style.display === "block";

        if (!isOpen) {
            targetOverlay.style.display = "block";
            card.style.overflow = "visible";
            card.style.zIndex = "2000"; // Vor alle anderen Karten bringen
        } else {
            targetOverlay.style.display = "none";
            // Z-Index nur zurücksetzen, wenn gar kein Fenster mehr offen ist
            const anyOpen = Array.from(allOverlays).some(ov => ov.style.display === "block");
            if (!anyOpen) card.style.zIndex = "1000";
        }
    };
    // =================================================
    // SEQUENTIELLER GLOW-EFFEKT
    // =================================================

    function runGlowSequence(card) {
        const buttons = [
            card.querySelector('.live-link'),
            card.querySelector('.structure'),
            card.querySelector('.info')
        ];

        buttons.forEach((btn, index) => {
            if (!btn) return;
            setTimeout(() => {
                btn.classList.add('glow');
                setTimeout(() => {
                    btn.classList.remove('glow');
                }, 300); // Wie lange ein Button leuchtet
            }, index * 200); // Verzögerung zwischen den Buttons
        });
    }

    // Event-Listener für Klicks auf die Karte (aber nicht auf die Buttons selbst)
    items.forEach(item => {
        item.addEventListener('click', function(e) {
            // Wenn der Klick NICHT auf einem Button oder dem Close-X war
            if (!e.target.closest('.card-btn') && !e.target.closest('.close-info')) {
                runGlowSequence(this);
            }
        });
    });

})();