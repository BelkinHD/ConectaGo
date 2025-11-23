let cropper;
const profileImage = document.getElementById('profileImage');
const fileInput = document.getElementById('id_foto');
const cropperModal = document.getElementById('cropperModal');
const imageToCrop = document.getElementById('imageToCrop');

fileInput.addEventListener('change', function(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    const file = files[0];
    const url = URL.createObjectURL(file);
    imageToCrop.src = url;
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
});

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
    const croppedFile = new File([blob], fileInput.files[0].name, { type: 'image/png' });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(croppedFile);
    fileInput.files = dataTransfer.files;

    // Update preview image
    profileImage.src = URL.createObjectURL(croppedFile);

    cropperModal.classList.add('hidden');
  }, 'image/png');
});

// Optional: prevent form submission if cropping modal is open
document.getElementById('profileForm').addEventListener('submit', (e) => {
  if (!fileInput.files.length) {
    // No file selected, allow submit
    return;
  }
  if (!cropperModal.classList.contains('hidden')) {
    e.preventDefault();
    alert('Por favor, confirme o cancele el recorte de la imagen antes de enviar el formulario.');
  }
});
