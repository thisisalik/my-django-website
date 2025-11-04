document.addEventListener('DOMContentLoaded', () => {
    const pic = document.getElementById('profilePic');
    const modal = document.getElementById('picModal');
    const modalImg = document.getElementById('modalImg');
    if (!pic || !modal || !modalImg) return;
  
    pic.addEventListener('click', () => { modal.style.display = 'flex'; });
    modal.addEventListener('click', () => { modal.style.display = 'none'; });
  });
  