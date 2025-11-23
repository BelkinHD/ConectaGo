document.addEventListener('DOMContentLoaded', function () {
  const bellButton = document.getElementById('notification-bell');
  const dropdown = document.getElementById('notification-dropdown');

  if (bellButton && dropdown) {
    bellButton.addEventListener('click', function (event) {
      event.stopPropagation();
      const isHidden = dropdown.classList.contains('hidden');
      if (isHidden) {
        dropdown.classList.remove('hidden');
        bellButton.setAttribute('aria-expanded', 'true');
      } else {
        dropdown.classList.add('hidden');
        bellButton.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('click', function (event) {
      if (!bellButton.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
        bellButton.setAttribute('aria-expanded', 'false');
      }
    });
  }
});
