// ── Theme Toggle ─────────────────────────────────────────────────
const html = document.documentElement;
const saved = localStorage.getItem('rootcare-theme') || 'light';
html.setAttribute('data-theme', saved);

document.getElementById('themeToggle')?.addEventListener('click', () => {
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('rootcare-theme', next);
});

// ── Mobile Menu ───────────────────────────────────────────────────
document.getElementById('navBurger')?.addEventListener('click', () => {
  document.getElementById('navLinks')?.classList.toggle('open');
});

// ── Animated Counters ─────────────────────────────────────────────
function animateCounter(el) {
  const target = parseInt(el.dataset.target) || 0;
  const suffix = el.dataset.suffix || '';
  const duration = 1800;
  const start = performance.now();

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(target * eased);
    el.textContent = current + suffix;
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target + suffix;
  }
  requestAnimationFrame(update);
}

// Lancer les compteurs visibles
function initCounters() {
  document.querySelectorAll('.counter').forEach(el => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(el);
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    observer.observe(el);
  });
}

// ── Scroll Animations ─────────────────────────────────────────────
function initScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.animate-fadein-scroll').forEach(el => {
    observer.observe(el);
  });
}

// ── Score Arc Animation ───────────────────────────────────────────
function animateScoreArc() {
  const arc = document.getElementById('scoreArc');
  if (!arc) return;
  const score = parseInt(arc.dataset.score) || 0;
  const max   = parseInt(arc.dataset.max) || 80;
  const circumference = 314;
  const targetOffset = circumference - (circumference * score / max);

  // Start fully offset (empty)
  arc.style.strokeDashoffset = circumference;

  setTimeout(() => {
    arc.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4,0,0.2,1)';
    arc.style.strokeDashoffset = targetOffset;
  }, 400);
}

// ── Animated Bars ─────────────────────────────────────────────────
function initAnimatedBars() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bars = entry.target.querySelectorAll('.animated-bar');
        bars.forEach((bar, i) => {
          setTimeout(() => {
            bar.style.width = bar.dataset.width;
          }, i * 150);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.detail-grid').forEach(el => observer.observe(el));
}

// ── Flash Auto-dismiss ────────────────────────────────────────────
function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(20px)';
      flash.style.transition = 'all 0.3s ease';
      setTimeout(() => flash.remove(), 300);
    }, 4000);
  });
}

// ── Navbar scroll effect ──────────────────────────────────────────
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  window.addEventListener('scroll', () => {
    navbar.style.boxShadow = window.scrollY > 20
      ? '0 2px 20px rgba(0,0,0,0.1)'
      : 'none';
  }, { passive: true });
}

// ── Form Steps Navigation ─────────────────────────────────────────
const fieldLabels = {
  'nb_repas': 'Combien de repas mangez-vous par jour ?',
  'fruits_legumes': 'À quelle fréquence mangez-vous des fruits et légumes ?',
  'eau_par_jour': 'Combien de litres d\'eau buvez-vous par jour ?',
  'activite_physique': 'À quelle fréquence faites-vous de l\'activité physique ?',
  'heures_sommeil': 'Combien d\'heures dormez-vous par nuit ?',
  'qualite_sommeil': 'Comment évaluez-vous la qualité de votre sommeil ?',
  'tabac': 'Consommez-vous du tabac ?',
  'alcool': 'Consommez-vous de l\'alcool ?',
  'niveau_stress': 'Quel est votre niveau de stress quotidien ?'
};

function showStep(stepNumber) {
  // Hide all steps
  document.querySelectorAll('.form-step').forEach(step => {
    step.classList.remove('active');
  });
  // Show target step
  document.getElementById('step' + stepNumber).classList.add('active');
  // Update progress indicators
  document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
    if (index + 1 <= stepNumber) {
      indicator.classList.add('active');
    } else {
      indicator.classList.remove('active');
    }
  });
}

function validateStep(stepNumber) {
  const step = document.getElementById('step' + stepNumber);
  const requiredNames = {
    1: ['nb_repas', 'fruits_legumes', 'eau_par_jour'],
    2: ['activite_physique', 'heures_sommeil', 'qualite_sommeil'],
    3: ['tabac', 'alcool', 'niveau_stress']
  };
  const names = requiredNames[stepNumber] || [];
  let missing = [];
  names.forEach(name => {
    const inputs = step.querySelectorAll(`input[name="${name}"]`);
    if (inputs.length > 0) {
      if (inputs[0].type === 'radio') {
        const anyChecked = Array.from(inputs).some(radio => radio.checked);
        if (!anyChecked) {
          missing.push(name);
          inputs.forEach(radio => radio.closest('.radio-card').classList.add('error'));
        } else {
          inputs.forEach(radio => radio.closest('.radio-card').classList.remove('error'));
        }
      } else if (inputs[0].type === 'range') {
        // Range always has value
      }
    }
  });
  return missing.length === 0 ? true : missing;
}

function nextStep(stepNumber) {
  const currentStep = stepNumber - 1;
  const validation = validateStep(currentStep);
  if (validation === true) {
    showStep(stepNumber);
  } else {
    alert('Vous devez répondre aux questions suivantes : ' + validation.map(name => fieldLabels[name] || name).join(', '));
  }
}

function prevStep(stepNumber) {
  showStep(stepNumber);
}

// ── Range Input Updates ───────────────────────────────────────────
function updateRange(input, valueId) {
  const value = input.value;
  document.getElementById(valueId).textContent = value + ' / 5';
  const dots = input.parentElement.querySelectorAll('.range-dot');
  dots.forEach((dot, index) => {
    if (index + 1 <= value) {
      dot.classList.add('active');
    } else {
      dot.classList.remove('active');
    }
  });
}

// ── Init all ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCounters();
  initScrollAnimations();
  animateScoreArc();
  initAnimatedBars();
  initFlashDismiss();
  initNavbarScroll();

  // Form validation on submit
  const form = document.getElementById('healthForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      for (let i = 1; i <= 3; i++) {
        const validation = validateStep(i);
        if (validation !== true) {
          e.preventDefault();
          showStep(i);
          alert('Vous devez répondre aux questions suivantes dans l\'étape ' + i + ' : ' + validation.map(name => fieldLabels[name] || name).join(', '));
          return;
        }
      }
    });
  }
});