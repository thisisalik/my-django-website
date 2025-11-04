(function () {
    function setWorker() {
      if (!window.pdfjsLib) return false;
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/vendor/pdfjs/pdf.worker.min.js';
      return true;
    }
  
    function initCard(card) {
      const gid = card.getAttribute('data-gid');
      const url = card.getAttribute('data-pdf-url');
      const canvas = document.getElementById(`pdfCanvas-${gid}`);
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
  
      const prevBtn   = card.querySelector(`.pdf-prev[data-gid="${gid}"]`);
      const nextBtn   = card.querySelector(`.pdf-next[data-gid="${gid}"]`);
      const zoomInBtn = card.querySelector(`.pdf-zoom-in[data-gid="${gid}"]`);
      const zoomOutBtn= card.querySelector(`.pdf-zoom-out[data-gid="${gid}"]`);
      const fitBtn    = card.querySelector(`.pdf-fit[data-gid="${gid}"]`);
      const zoomLabel = card.querySelector(`.pdf-zoom-label[data-gid="${gid}"]`);
      const pageLabel = card.querySelector(`.pdf-page-label[data-gid="${gid}"]`);
  
      let pdfDoc = null, pageNum = 1, pageCount = 1, baseScale = 1, scale = 1, rendering = false;
  
      function updateLabels() {
        if (zoomLabel) zoomLabel.textContent = Math.round(scale * 100) + '%';
        if (pageLabel) pageLabel.textContent = pageNum + ' / ' + pageCount;
        if (prevBtn) prevBtn.disabled = (pageNum <= 1);
        if (nextBtn) nextBtn.disabled = (pageNum >= pageCount);
      }
  
      function fitToWidth(page) {
        const wrap = card.querySelector('.pdf-canvas-wrap');
        const available = wrap.clientWidth - 2;
        const viewport1 = page.getViewport({ scale: 1 });
        baseScale = available / viewport1.width;
        scale = baseScale;
      }
  
      function renderPage() {
        if (rendering) return;
        rendering = true;
        pdfDoc.getPage(pageNum).then(page => {
          if (baseScale === 1) fitToWidth(page);
          const vp = page.getViewport({ scale });
          canvas.style.width = Math.round(vp.width) + 'px';
          canvas.style.height = Math.round(vp.height) + 'px';
          canvas.width = Math.round(vp.width * dpr);
          canvas.height = Math.round(vp.height * dpr);
          const transform = dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null;
          return page.render({ canvasContext: ctx, viewport: vp, transform }).promise;
        }).finally(() => { rendering = false; updateLabels(); });
      }
  
      function start() {
        window.pdfjsLib.getDocument(url).promise.then(doc => {
          pdfDoc = doc; pageCount = doc.numPages; pageNum = 1;
          renderPage();
  
          if ('ResizeObserver' in window) {
            const ro = new ResizeObserver(() => { baseScale = 1; renderPage(); });
            ro.observe(card);
          } else {
            window.addEventListener('resize', () => { baseScale = 1; renderPage(); });
          }
        }).catch(console.error);
      }
  
      // controls
      if (zoomInBtn)  zoomInBtn.addEventListener('click', () => { scale = Math.min(scale + 0.15, 4); renderPage(); });
      if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => { scale = Math.max(scale - 0.15, 0.4); renderPage(); });
      if (fitBtn)     fitBtn.addEventListener('click', () => { baseScale = 1; renderPage(); });
      if (prevBtn)    prevBtn.addEventListener('click', () => { if (pageNum > 1) { pageNum--; renderPage(); } });
      if (nextBtn)    nextBtn.addEventListener('click', () => { if (pageNum < pageCount) { pageNum++; renderPage(); } });
  
      start();
    }
  
    document.addEventListener('DOMContentLoaded', () => {
      if (!setWorker()) return;
      document.querySelectorAll('.pdf-card[data-pdf-url]').forEach(initCard);
    });
  })();
  