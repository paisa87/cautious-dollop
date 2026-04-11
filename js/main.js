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
      const cats = card.dataset.category ? card.dataset.category.split(' ') : [];
      card.classList.toggle('hidden', filter !== 'all' && !cats.includes(filter));
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

// ==========================================
// GUESTBOOK FORM — AJAX submission via Formspree
// ==========================================
const guestForm  = document.getElementById('guestbookForm');
const gbSubmit   = document.getElementById('gbSubmit');
const gbError    = document.getElementById('gbError');

if (guestForm) {
  guestForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (gbSubmit) { gbSubmit.disabled = true; gbSubmit.textContent = 'Sending\u2026'; }
    if (gbError)  { gbError.style.display = 'none'; }

    try {
      const resp = await fetch(guestForm.action, {
        method: 'POST',
        body: new FormData(guestForm),
        headers: { 'Accept': 'application/json' }
      });

      if (resp.ok) {
        guestForm.innerHTML =
          '<p class="guestbook-success">' +
          '\u2728 Entry received \u2014 thanks for signing the guestbook! \u2728' +
          '</p>';
      } else {
        const data = await resp.json().catch(() => ({}));
        const msg = (data.errors || []).map(x => x.message).join(', ') ||
                    'Something went wrong. Please try emailing paisa@vgcc.edu instead.';
        if (gbError) { gbError.textContent = msg; gbError.style.display = 'block'; }
        if (gbSubmit) { gbSubmit.disabled = false; gbSubmit.textContent = '\u270D Submit Entry'; }
      }
    } catch {
      if (gbError) {
        gbError.textContent = 'Network error. Please try emailing paisa@vgcc.edu instead.';
        gbError.style.display = 'block';
      }
      if (gbSubmit) { gbSubmit.disabled = false; gbSubmit.textContent = '\u270D Submit Entry'; }
    }
  });
}

// ==========================================
// STORYBOOK 3 — PASSWORD UNLOCK
// Password = AGTCAG (5' → 3' left strand of DNA helix)
// ==========================================
const SB3_PASSWORD = 'AGTCAG';
const sb3Input    = document.getElementById('sb3Password');
const sb3Submit   = document.getElementById('sb3Submit');
const sb3Locked   = document.getElementById('sb3Locked');
const sb3Unlocked = document.getElementById('sb3Unlocked');

function unlockSb3() {
  if (sb3Locked)   sb3Locked.style.display   = 'none';
  if (sb3Unlocked) sb3Unlocked.style.display = 'block';
  sessionStorage.setItem('sb3Unlocked', '1');
}

function checkSb3Password() {
  if (!sb3Input) return;
  if (sb3Input.value.trim().toUpperCase() === SB3_PASSWORD) {
    unlockSb3();
  } else {
    sb3Input.classList.add('sb3-error');
    const orig = sb3Input.placeholder;
    sb3Input.value = '';
    sb3Input.placeholder = 'Wrong sequence \u2014 try again';
    setTimeout(() => {
      sb3Input.classList.remove('sb3-error');
      sb3Input.placeholder = orig;
    }, 1600);
  }
}

if (sb3Submit) sb3Submit.addEventListener('click', checkSb3Password);
if (sb3Input) {
  sb3Input.addEventListener('keydown', e => {
    if (e.key === 'Enter') checkSb3Password();
  });
  // Restore unlocked state within the same browser session
  if (sessionStorage.getItem('sb3Unlocked') === '1') unlockSb3();
}
