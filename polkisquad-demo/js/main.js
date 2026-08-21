// Polki Squad — main.js v0.1
// Demo static site interactions: counter animation, newsletter form, smooth scroll.

(function() {
    'use strict';

    // 1. Counter animation (for stats strip)
    const counters = document.querySelectorAll('.stat__number[data-target]');
    const animateCounter = (el) => {
        const target = parseInt(el.getAttribute('data-target'), 10);
        const duration = 1500;
        const start = performance.now();

        const step = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            const value = Math.floor(eased * target);
            el.textContent = value.toLocaleString('es-PY');
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target.toLocaleString('es-PY');
        };
        requestAnimationFrame(step);
    };

    // Use IntersectionObserver to animate when visible
    if ('IntersectionObserver' in window && counters.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });
        counters.forEach(c => observer.observe(c));
    }

    // 2. Newsletter form (demo: just show thank-you, no backend)
    const nlForm = document.querySelector('.newsletter__form');
    if (nlForm) {
        nlForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = nlForm.querySelector('.newsletter__input');
            const value = input.value.trim();
            if (!value || !value.includes('@')) {
                input.focus();
                input.style.boxShadow = '0 0 0 3px rgba(220, 53, 69, 0.5)';
                setTimeout(() => { input.style.boxShadow = ''; }, 2000);
                return;
            }
            nlForm.innerHTML = '<p style="color:white;font-size:1.125rem;font-weight:500;">¡Gracias por suscribirte! 🐾 Te escribimos pronto.</p>';
        });
    }

    // 3. Fade-in on scroll (for animal cards, way cards, etc.)
    // Only hide if JS is ready (preventing content invisible if JS fails)
    const fadeEls = document.querySelectorAll('.animal-card, .way-card, .mission__content, .mission__visual');
    if ('IntersectionObserver' in window && fadeEls.length) {
        // Mark body so CSS can hide elements
        document.body.classList.add('js-animations-ready');
        const fadeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    fadeObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });
        fadeEls.forEach(el => fadeObserver.observe(el));
    }

    // 4. Respect prefers-reduced-motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.body.classList.add('reduce-motion');
    }

    // 4. Add visible class to body when JS is ready (for CSS hooks)
    document.body.classList.add('js-ready');

})();


// 5. Service Worker registration (PWA)
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then((reg) => {
            console.log('[SW] Registered:', reg.scope);
        }).catch((err) => {
            console.warn('[SW] Registration failed:', err);
        });
    });
}


// 6. Back to top button
const backToTop = document.getElementById('back-to-top');
if (backToTop) {
    const toggleVisibility = () => {
        if (window.scrollY > 400) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    };
    window.addEventListener('scroll', toggleVisibility, { passive: true });
    toggleVisibility();
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}


// 7. Dismissible demo banner (localStorage remembers choice)
const banner = document.getElementById('demo-banner');
const bannerClose = document.getElementById('demo-banner-close');
if (banner && bannerClose) {
    if (localStorage.getItem('polkisquad-banner-dismissed') === '1') {
        banner.classList.add('hidden');
    }
    bannerClose.addEventListener('click', () => {
        banner.classList.add('hidden');
        localStorage.setItem('polkisquad-banner-dismissed', '1');
    });
}

// 8. Floating outreach CTA (collapsible)
const outreachCta = document.querySelector('.outreach-cta');
if (outreachCta) {
    const toggleBtn = outreachCta.querySelector('.outreach-cta__button');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            // If it's a link, don't toggle
            if (toggleBtn.tagName === 'A') return;
            e.preventDefault();
            outreachCta.classList.toggle('open');
        });
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!outreachCta.contains(e.target)) {
                outreachCta.classList.remove('open');
            }
        });
    }
}


// 9. Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const primaryNav = document.getElementById('primary-nav');
if (navToggle && primaryNav) {
    navToggle.addEventListener('click', () => {
        const isOpen = primaryNav.classList.toggle('nav--open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && primaryNav.classList.contains('nav--open')) {
            primaryNav.classList.remove('nav--open');
            navToggle.setAttribute('aria-expanded', 'false');
        }
    });
}
