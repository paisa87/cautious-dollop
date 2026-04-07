// ==========================================
// NAV: shadow on scroll + mobile toggle
// ==========================================
const navbar = document.getElementById('navbar');
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.getElementById('navLinks');

if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 10);
  }, { passive: true });
}

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', open);
  });
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// ==========================================
// USE CASE FILTER TABS
// ==========================================
const tabs = document.querySelectorAll('.tab');
const cards = document.querySelectorAll('.use-card');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');

    const filter = tab.dataset.filter;
    cards.forEach(card => {
      card.classList.toggle('hidden', filter !== 'all' && card.dataset.category !== filter);
    });
  });
});

// ==========================================
// ACTIVE NAV LINK on scroll
// ==========================================
const sections = document.querySelectorAll('section[id], header[id]');
const navAnchors = document.querySelectorAll('.nav-links a');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      navAnchors.forEach(a => {
        a.classList.toggle('active-link', a.getAttribute('href') === `#${id}`);
      });
    }
  });
}, { threshold: 0.3 });

sections.forEach(s => observer.observe(s));

// ==========================================
// VISITOR COUNTER (fun fake counter)
// ==========================================
const countEl = document.getElementById('visitorCount');
if (countEl) {
  const base = 1337;
  const stored = parseInt(sessionStorage.getItem('visitCount') || base, 10);
  const count = stored + Math.floor(Math.random() * 3);
  sessionStorage.setItem('visitCount', count);
  countEl.textContent = count.toLocaleString();
}

// ==========================================
// EASTER EGG — KONAMI CODE
// ↑ ↑ ↓ ↓ ← → ← → B A
// ==========================================
const KONAMI = [
  'ArrowUp','ArrowUp','ArrowDown','ArrowDown',
  'ArrowLeft','ArrowRight','ArrowLeft','ArrowRight',
  'b','a'
];
let konamiProgress = 0;

const easterEgg = document.getElementById('easterEgg');
const eeClose   = document.getElementById('eeClose');

function openEasterEgg() {
  if (!easterEgg) return;
  easterEgg.classList.add('active');
  easterEgg.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  eeClose && eeClose.focus();
}

function closeEasterEgg() {
  if (!easterEgg) return;
  easterEgg.classList.remove('active');
  easterEgg.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  konamiProgress = 0;
}

document.addEventListener('keydown', e => {
  // Close on Escape
  if (e.key === 'Escape') { closeEasterEgg(); return; }

  // Track Konami sequence
  if (e.key === KONAMI[konamiProgress]) {
    konamiProgress++;
    if (konamiProgress === KONAMI.length) {
      konamiProgress = 0;
      openEasterEgg();
    }
  } else {
    // Allow restarting from beginning if first key matches
    konamiProgress = (e.key === KONAMI[0]) ? 1 : 0;
  }
});

if (eeClose) {
  eeClose.addEventListener('click', closeEasterEgg);
}

// Click backdrop (outside modal) to close
if (easterEgg) {
  easterEgg.addEventListener('click', e => {
    if (e.target === easterEgg) closeEasterEgg();
  });
}
