// ✅ Modal Image Viewer Script
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.style.display = 'none';
    modal.style.position = 'fixed';
    modal.style.top = 0;
    modal.style.left = 0;
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    modal.style.zIndex = 9999;
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.padding = '20px';
    modal.innerHTML = '<img id="modalImg" style="max-width: 90%; max-height: 90%; border-radius: 12px;">';
  
    document.body.appendChild(modal);
  
    const modalImg = document.getElementById('modalImg');
  
    document.querySelectorAll('.clickable-image').forEach(img => {
      img.addEventListener('click', () => {
        modal.style.display = 'flex';
        modalImg.src = img.src;
      });
    });
  
    modal.addEventListener('click', () => {
      modal.style.display = 'none';
      modalImg.src = '';
    });
  });
  