/*
 * BeautyFull — JS del shell visual (R5.1).
 * Única responsabilidad: toggle del menú de la navbar en móvil.
 * Mejora progresiva: sin JavaScript el menú permanece visible (ver main.css),
 * de modo que la navbar renderizada en servidor sigue siendo usable; el JS
 * solo colapsa/expande el menú en pantallas pequeñas.
 */
(function () {
    'use strict';

    // Marca el documento como "con JS" para que el CSS pueda colapsar el menú
    // en móvil SOLO cuando el toggle es operable. Sin JS, el menú permanece
    // visible y la navegación sigue siendo usable (mejora progresiva).
    document.documentElement.classList.add('js');

    function initNavbarToggle() {
        var toggle = document.querySelector('[data-navbar-toggle]');
        var menu = document.querySelector('[data-navbar-menu]');

        if (!toggle || !menu) {
            return;
        }

        toggle.addEventListener('click', function () {
            var isOpen = menu.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavbarToggle);
    } else {
        initNavbarToggle();
    }
})();
