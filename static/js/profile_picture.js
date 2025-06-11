document.addEventListener('DOMContentLoaded', function () {
  const picInput = document.getElementById('id_profile_picture');
  const picPreview = document.getElementById('current-profile-pic');

  if (picInput && picPreview) {
    picInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          picPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }
});
