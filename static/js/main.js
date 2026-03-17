/* ══════════════════════════════════════
   AdVance Platform – Main JS
   ══════════════════════════════════════ */

// ── Mobile nav toggle ──
function toggleNav() {
  document.getElementById('navLinks').classList.toggle('open');
}

// ── Countdown timers for ad cards ──
function initExpiryTimers() {
  document.querySelectorAll('[data-expiry]').forEach(el => {
    const expiry = new Date(el.dataset.expiry + 'Z'); // treat as UTC
    const label  = el.querySelector('.expiry-label') || el;
    updateTimer(label, expiry);
    setInterval(() => updateTimer(label, expiry), 60_000);
  });
}

function updateTimer(el, expiry) {
  const now  = new Date();
  const diff = expiry - now;

  if (diff <= 0) {
    el.textContent = 'Expired';
    el.style.color = 'var(--text-3)';
    return;
  }

  const days  = Math.floor(diff / 86_400_000);
  const hours = Math.floor((diff % 86_400_000) / 3_600_000);
  const mins  = Math.floor((diff % 3_600_000)  / 60_000);

  if (days > 0) {
    el.textContent = `${days}d ${hours}h left`;
  } else if (hours > 0) {
    el.textContent = `${hours}h ${mins}m left`;
    if (hours < 6) el.style.color = '#fbbf24'; // warn color
  } else {
    el.textContent = `${mins}m left`;
    el.style.color = '#f87171'; // urgent color
  }
}

// ── Smooth card entrance animation ──
function initCardAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity   = '1';
            entry.target.style.transform = 'translateY(0)';
          }, i * 60);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08 }
  );

  document.querySelectorAll('.ad-card, .cat-card, .step-card, .dash-stat').forEach(card => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(22px)';
    card.style.transition = 'opacity 0.45s ease, transform 0.45s ease, border-color 0.25s, box-shadow 0.25s';
    observer.observe(card);
  });
}

// ── Auto-dismiss flash messages after 5s ──
function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity    = '0';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
}

// ── Stat number counter animation ──
function animateCounters() {
  document.querySelectorAll('.dash-stat-num, .stat-num').forEach(el => {
    const raw = el.textContent.replace(/[^0-9]/g, '');
    if (!raw || isNaN(raw)) return;
    const target = parseInt(raw);
    const suffix = el.textContent.replace(raw, '');
    if (target === 0) return;
    let current = 0;
    const step  = Math.ceil(target / 40);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current + suffix;
      if (current >= target) clearInterval(timer);
    }, 30);
  });
}

// ── Run everything on DOMContentLoaded ──
document.addEventListener('DOMContentLoaded', () => {
  initExpiryTimers();
  initCardAnimations();
  initFlashDismiss();
  setTimeout(animateCounters, 200);
});
