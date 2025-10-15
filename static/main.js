document.addEventListener('DOMContentLoaded', () => {
  const menuButton = document.getElementById('mobile-menu-button');
  const mobileNav = document.getElementById('mobile-navigation');

  if (menuButton && mobileNav) {
    menuButton.addEventListener('click', () => {
      const expanded = menuButton.getAttribute('aria-expanded') === 'true';
      menuButton.setAttribute('aria-expanded', String(!expanded));
      mobileNav.classList.toggle('hidden');
    });
  }

  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach((flash) => {
    const dismiss = flash.querySelector('.flash-dismiss');
    if (dismiss) {
      dismiss.addEventListener('click', () => {
        flash.remove();
      });
    }
  });

  const backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        backToTop.classList.add('show');
      } else {
        backToTop.classList.remove('show');
      }
    });

    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  const saveButton = document.getElementById('schedule-save');
  const deleteButton = document.getElementById('schedule-delete');
  if (saveButton) {
    saveButton.addEventListener('click', () => {
      const name = window.prompt('Enter a name for this schedule:');
      if (!name) {
        return;
      }
      const favorite = window.confirm('Favorite this schedule?');
      const nameField = document.getElementById('scheduleName');
      const favoriteField = document.getElementById('scheduleFavorite');
      const form = document.getElementById('saveForm');
      if (nameField && favoriteField && form) {
        nameField.value = name;
        favoriteField.value = favorite ? '1' : '0';
        form.submit();
      }
    });
  }

  if (deleteButton) {
    deleteButton.addEventListener('click', () => {
      const destination = deleteButton.getAttribute('data-destination');
      if (destination && window.confirm('Discard this schedule and return home?')) {
        window.location.href = destination;
      }
    });
  }

  document.querySelectorAll('[data-slider]').forEach((slider) => {
    const track = slider.querySelector('.slider-track');
    const panels = slider.querySelectorAll('.slider-panel');
    const dots = slider.querySelectorAll('.slider-dot');
    if (!track || panels.length === 0) {
      return;
    }

    let currentIndex = 0;
    const update = () => {
      track.style.transform = `translateX(-${currentIndex * 100}%)`;
      dots.forEach((dot, index) => {
        const isActive = index === currentIndex;
        dot.classList.toggle('is-active', isActive);
        dot.setAttribute('aria-current', isActive ? 'true' : 'false');
      });
    };

    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => {
        currentIndex = index;
        update();
      });
    });

    update();

    let intervalId = window.setInterval(() => {
      currentIndex = (currentIndex + 1) % panels.length;
      update();
    }, 6000);

    slider.addEventListener('mouseenter', () => {
      window.clearInterval(intervalId);
    });

    slider.addEventListener('mouseleave', () => {
      intervalId = window.setInterval(() => {
        currentIndex = (currentIndex + 1) % panels.length;
        update();
      }, 6000);
    });
  });
});
