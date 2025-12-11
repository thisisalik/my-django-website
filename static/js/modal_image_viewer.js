document.addEventListener('DOMContentLoaded', function () {
  const modal = document.createElement('div');
  modal.id = 'imageModal';
  modal.style.display = 'none';
  modal.style.position = 'fixed';
  modal.style.top = 0;
  modal.style.left = 0;
  modal.style.width = '100%';
  modal.style.height = '100%';
  modal.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
  modal.style.zIndex = 9999;
  modal.style.justifyContent = 'center';
  modal.style.alignItems = 'center';
  modal.style.padding = '20px';

  modal.innerHTML = `
    <button id="prevModalBtn" style="position: absolute; left: 20px; top: 50%; transform: translateY(-50%); background: transparent; color: white; border: none; font-size: 40px; cursor: pointer;">⟨</button>
    <img id="modalImg" style="max-width: 90%; max-height: 90%; border-radius: 12px;">
    <button id="nextModalBtn" style="position: absolute; right: 20px; top: 50%; transform: translateY(-50%); background: transparent; color: white; border: none; font-size: 40px; cursor: pointer;">⟩</button>
  `;

  document.body.appendChild(modal);

  const modalImg = modal.querySelector('#modalImg');
  const prevBtn = modal.querySelector('#prevModalBtn');
  const nextBtn = modal.querySelector('#nextModalBtn');

  let currentGroupImages = [];
  let currentIndex = 0;

  function updateModalImage() {
    modalImg.src = currentGroupImages[currentIndex].src;

    // Toggle button visibility
    if (currentGroupImages.length <= 1) {
      prevBtn.style.display = 'none';
      nextBtn.style.display = 'none';
    } else {
      prevBtn.style.display = currentIndex === 0 ? 'none' : 'block';
      nextBtn.style.display = currentIndex === currentGroupImages.length - 1 ? 'none' : 'block';
    }
  }

  document.body.addEventListener('click', function (e) {
    if (e.target.classList.contains('clickable-image')) {
      const img = e.target;

      // Detect group class
      const groupClass = Array.from(img.parentNode.classList).find(cls => cls.startsWith('slide-group-'));
      if (groupClass) {
        currentGroupImages = Array.from(document.querySelectorAll(`.${groupClass} img`));
        currentIndex = currentGroupImages.findIndex(i => i.src === img.src);
      } else {
        currentGroupImages = [img];
        currentIndex = 0;
      }

      updateModalImage();
      modal.style.display = 'flex';
    }
  });

  nextBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (currentIndex < currentGroupImages.length - 1) {
      currentIndex++;
      updateModalImage();
    }
  });

  prevBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (currentIndex > 0) {
      currentIndex--;
      updateModalImage();
    }
  });

  modal.addEventListener('click', () => {
    modal.style.display = 'none';
    modalImg.src = '';
    currentGroupImages = [];
  });
});
