(function () {
    const current = {};
  
    function showSlide(groupId, index, total) {
      for (let i = 1; i <= total; i++) {
        const el = document.getElementById(`slide-${groupId}-${i}`);
        if (el) el.style.display = (i === index) ? 'block' : 'none';
      }
      const prevBtn = document.querySelector(`.prev-btn[data-group="${groupId}"]`);
      const nextBtn = document.querySelector(`.next-btn[data-group="${groupId}"]`);
      if (prevBtn) prevBtn.style.display = index === 1 ? 'none' : 'block';
      if (nextBtn) nextBtn.style.display = index === total ? 'none' : 'block';
      current[groupId] = index;
    }
  
    document.addEventListener('DOMContentLoaded', () => {
      // init all groups
      document.querySelectorAll('.letter-image-group').forEach(group => {
        const gid = group.getAttribute('data-group');
        const total = group.querySelectorAll(`.slide-group-${gid}`).length;
        showSlide(gid, 1, total);
      });
  
      // delegate clicks for nav
      document.body.addEventListener('click', (e) => {
        const prev = e.target.closest('.prev-btn');
        const next = e.target.closest('.next-btn');
        if (!prev && !next) return;
  
        const gid = (prev || next).getAttribute('data-group');
        const total = document.querySelectorAll(`.slide-group-${gid}`).length;
        const cur = current[gid] || 1;
  
        if (prev && cur > 1) showSlide(gid, cur - 1, total);
        if (next && cur < total) showSlide(gid, cur + 1, total);
      });
    });
  })();
  