// Smooth scrolling and active menu link highlighting
const menuLinks = document.querySelectorAll('.section-menu a');
const sections = ['about', 'prices', 'experience', 'schedule', 'reviews'];

function scrollToSection(event, sectionId) {
  event.preventDefault();
  const yOffset = -80;
  const element = document.getElementById(sectionId);
  const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
  window.scrollTo({ top: y, behavior: 'smooth' });
  setActiveLink(sectionId);
}

function setActiveLink(sectionId) {
  menuLinks.forEach(link => {
    if (link.getAttribute('href') === '#' + sectionId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(sectionId => {
    const section = document.getElementById(sectionId);
    const sectionTop = section.offsetTop - 100;
    if (window.pageYOffset >= sectionTop) {
      current = sectionId;
    }
  });
  setActiveLink(current);
});
