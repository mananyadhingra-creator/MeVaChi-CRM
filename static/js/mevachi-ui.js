/**
 * MeVaChi CRM — UI Enhancements
 * Scroll preservation + Bootstrap modal fixes
 */
(function () {
    'use strict';

    var SCROLL_PREFIX = 'mevachi_scroll_';

    function scrollKey() {
        return SCROLL_PREFIX + window.location.pathname;
    }

    function saveScroll() {
        try {
            sessionStorage.setItem(scrollKey(), String(window.scrollY || window.pageYOffset || 0));
        } catch (e) { /* private browsing */ }
    }

    function restoreScroll() {
        try {
            var saved = sessionStorage.getItem(scrollKey());
            if (saved === null) return;

            var y = parseInt(saved, 10);
            if (isNaN(y)) return;

            var attempts = 0;
            function apply() {
                window.scrollTo(0, y);
                attempts += 1;
                if (attempts < 6 && Math.abs((window.scrollY || 0) - y) > 2) {
                    requestAnimationFrame(apply);
                }
            }

            requestAnimationFrame(apply);
            setTimeout(apply, 50);
            setTimeout(apply, 150);
            setTimeout(apply, 350);
        } catch (e) { /* ignore */ }
    }

    /**
     * Move all Bootstrap modals to <body> so fixed positioning,
     * backdrop, and form submission work inside themed layouts.
     */
    function relocateModals() {
        var modals = document.querySelectorAll('.modal.fade');
        for (var i = 0; i < modals.length; i++) {
            var modal = modals[i];
            if (modal.parentElement !== document.body) {
                document.body.appendChild(modal);
            }
        }
    }

    function init() {
        relocateModals();
        restoreScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.addEventListener('load', restoreScroll);

    var scrollTimer;
    window.addEventListener('scroll', function () {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(saveScroll, 120);
    }, { passive: true });

    window.addEventListener('beforeunload', saveScroll);
    window.addEventListener('pagehide', saveScroll);

    document.addEventListener('submit', function (ev) {
        var form = ev.target;
        if (form && form.closest && form.closest('.modal')) {
            return;
        }
        saveScroll();
    }, true);

    document.addEventListener('change', function (ev) {
        var el = ev.target;
        if (!el || el.tagName !== 'SELECT') return;

        var form = el.closest('form');
        if (!form) return;

        var method = (form.getAttribute('method') || 'get').toLowerCase();
        var willSubmit = el.hasAttribute('onchange') &&
            el.getAttribute('onchange').indexOf('submit') !== -1;

        if (method === 'get' || willSubmit) {
            saveScroll();
        }
    }, true);

    document.addEventListener('click', function (ev) {
        var link = ev.target.closest('a[href]');
        if (!link) return;
        if (link.getAttribute('target') === '_blank') return;
        if (link.getAttribute('href').charAt(0) === '#') return;
        saveScroll();
    }, true);

})();

// ============================
// PASSWORD TOGGLE
// ============================

function togglePassword(id, icon){

    const input=document.getElementById(id);

    if(input.type==="password"){

        input.type="text";

        icon.classList.remove("bi-eye");

        icon.classList.add("bi-eye-slash");

    }

    else{

        input.type="password";

        icon.classList.remove("bi-eye-slash");

        icon.classList.add("bi-eye");

    }

}