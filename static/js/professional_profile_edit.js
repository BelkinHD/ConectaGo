// Dropdown and certification fields behavior
document.addEventListener('DOMContentLoaded', function() {
  const dropdownBtn = document.getElementById('especialidad-dropdown-btn');
  const dropdownContent = document.getElementById('especialidad-dropdown-content');
  const dropdownSearch = document.getElementById('especialidad-dropdown-search');
  const hiddenInput = document.getElementById('id_especialidad');
  const placeholderText = "Seleccione una especialidad";

  // Initialize button text
  if (hiddenInput.value) {
    const selectedItem = Array.from(dropdownContent.querySelectorAll('.dropdown-item')).find(item => item.dataset.value === hiddenInput.value);
    if (selectedItem) {
      dropdownBtn.textContent = selectedItem.textContent;
    }
  } else {
    dropdownBtn.textContent = placeholderText;
  }

  // Toggle dropdown visibility
  dropdownBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    dropdownContent.classList.toggle('show');
    dropdownSearch.value = '';
    filterItems('');
    dropdownSearch.focus();
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function() {
    dropdownContent.classList.remove('show');
  });

  // Filter dropdown items based on search input
  dropdownSearch.addEventListener('input', function() {
    filterItems(this.value);
  });

  function filterItems(searchTerm) {
    const lowerSearch = searchTerm.toLowerCase();
    dropdownContent.querySelectorAll('.dropdown-item').forEach(item => {
      if (item.textContent.toLowerCase().includes(lowerSearch)) {
        item.style.display = '';
      } else {
        item.style.display = 'none';
      }
    });
  }

  // Handle item selection
  dropdownContent.querySelectorAll('.dropdown-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.stopPropagation();
      dropdownBtn.textContent = this.textContent;
      hiddenInput.value = this.dataset.value;
      dropdownContent.classList.remove('show');
      hiddenInput.dispatchEvent(new Event('change'));
    });
  });

  
  // Hide certification fields if needed based on selected value
  const certFields = document.getElementById('certification_fields');
  function checkEspecialidad() {
    if (!certFields) return;
    const value = hiddenInput.value.toLowerCase();
    const requiresCert = [
      'electricidad',
      'instalador eléctrico clase d',
      'instalador eléctrico clase c, b o a',
      'técnico en mantenimiento de tableros eléctricos',
      'instalador de sistemas de puesta a tierra',
      'instalador de portones automáticos',
      'técnico en domótica',
      'instalador de iluminación led profesional',
      'gasfitería con gas',
      'instalador de artefactos a gas',
      'instalador de redes de gas interior',
      'reparador de fugas de gas domiciliarias',
      'instalador de calefactores de tiro balanceado o forzado',
      'técnico en detección de fugas o presión de red de gas',
      'climatización y refrigeración',
      'técnico en instalación de aire acondicionado tipo split',
      'técnico en instalación de calefacción central o calderas',
      'instalador de sistemas vrf o multi split',
      'técnico en cámaras de refrigeración',
      'manipulador de gases refrigerantes',
      'energías renovables',
      'instalador de paneles solares fotovoltaicos',
      'instalador de termos solares',
      'técnico en sistemas híbridos solares + red eléctrica',
      'instalador de inversores y sistemas solares conectados a red',
      'construcción y estructuras',
      'albañil estructural',
      'instalador de techumbres o cubiertas metálicas',
      'constructor de ampliaciones con permiso municipal',
      'instalador de ventanas termo-panel certificadas',
      'técnico en aislación térmica certificada',
      'elevadores y automatización',
      'técnico en mantenimiento de ascensores',
      'instalador de montacargas o salvaescalas',
      'técnico en sistemas automatizados de acceso',
      'seguridad y sistemas electrónicos',
      'instalador de cámaras de seguridad con red eléctrica',
      'instalador de sistemas de alarmas conectadas',
      'técnico en control de acceso biométrico o digital',
      'químicos, pesticidas y sanitización',
      'aplicador de plaguicidas',
      'desinfectador profesional'
    ];

    let show = false;
    for (const keyword of requiresCert) {
      if (value.includes(keyword)) {
        show = true;
        break;
      }
    }
    if (show) {
      certFields.style.display = 'block';
    } else {
      certFields.style.display = 'none';
    }
  }
  hiddenInput.addEventListener('change', checkEspecialidad);
  checkEspecialidad();
});


let cropper;
const profileImage = document.getElementById('profileImage');
const fileInput = document.getElementById('id_foto');
const cropperModal = document.getElementById('cropperModal');
const imageToCrop = document.getElementById('imageToCrop');

function openCropperModal(imageSrc) {
  imageToCrop.src = imageSrc;
  cropperModal.classList.remove('hidden');

  if (cropper) {
    cropper.destroy();
  }
  cropper = new Cropper(imageToCrop, {
    aspectRatio: 1,
    viewMode: 1,
    movable: true,
    zoomable: true,
    rotatable: true,
    scalable: true,
    autoCropArea: 1,
  });
}

fileInput.addEventListener('change', function(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    const file = files[0];
    const url = URL.createObjectURL(file);
    openCropperModal(url);
  }
});

if (profileImage) {
  profileImage.style.cursor = 'pointer';
  profileImage.addEventListener('click', () => {
    if (profileImage.src) {
      openCropperModal(profileImage.src);
    }
  });
}

document.getElementById('rotateLeft').addEventListener('click', () => {
  cropper.rotate(-90);
});

document.getElementById('rotateRight').addEventListener('click', () => {
  cropper.rotate(90);
});

document.getElementById('zoomIn').addEventListener('click', () => {
  cropper.zoom(0.1);
});

document.getElementById('zoomOut').addEventListener('click', () => {
  cropper.zoom(-0.1);
});

document.getElementById('resetCropper').addEventListener('click', () => {
  cropper.reset();
});

document.getElementById('cancelCrop').addEventListener('click', () => {
  cropperModal.classList.add('hidden');
  fileInput.value = '';
});

document.getElementById('confirmCrop').addEventListener('click', () => {
  cropper.getCroppedCanvas().toBlob((blob) => {
    const croppedFile = new File([blob], fileInput.files[0]?.name || 'cropped.png', { type: 'image/png' });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(croppedFile);
    fileInput.files = dataTransfer.files;

    // Update preview image
    profileImage.src = URL.createObjectURL(croppedFile);

    cropperModal.classList.add('hidden');
  }, 'image/png');
});

// Profile image preview update on file select
document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('id_foto');
  const profileImage = document.getElementById('profileImage');

  if (fileInput && profileImage) {
    fileInput.addEventListener('change', function(event) {
      const file = event.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          profileImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }
});

