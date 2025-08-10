// core/static/js/pdf_viewer.js
(function () {
    // Load pdf.js once
    function ensurePdfJs(cb) {
      if (window.pdfjsLib) return cb();
      const s = document.createElement("script");
      s.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
      s.onload = cb;
      document.head.appendChild(s);
    }
  
    function setWorker() {
      if (!window.pdfjsLib) return;
      window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    }
  
    // Render one viewer into a container
    async function mountPdfViewer(container, url, opts = {}) {
      const dpr = window.devicePixelRatio || 1;
  
      // build minimal markup inside container
      container.innerHTML = `
        <div class="pdf-card">
          <div class="pdf-toolbar">
            <button type="button" class="pdf-btn" data-act="prev">◀</button>
            <span class="pdf-badge" data-el="pageLabel">1 / 1</span>
            <button type="button" class="pdf-btn" data-act="next">▶</button>
            <span style="width:12px;"></span>
            <button type="button" class="pdf-btn" data-act="zoomOut">−</button>
            <span class="pdf-badge" data-el="zoomLabel">100%</span>
            <button type="button" class="pdf-btn" data-act="zoomIn">＋</button>
            <button type="button" class="pdf-btn" data-act="fit">Fit</button>
          </div>
          <div class="pdf-canvas-wrap"><canvas></canvas></div>
        </div>
      `;
  
      const canvas = container.querySelector("canvas");
      const ctx = canvas.getContext("2d");
      const pageLabel = container.querySelector('[data-el="pageLabel"]');
      const zoomLabel = container.querySelector('[data-el="zoomLabel"]');
      const wrap = container.querySelector(".pdf-canvas-wrap");
  
      // state
      let pdfDoc = null, pageNum = 1, pageCount = 1, baseScale = 1, scale = 1, rendering = false;
  
      function updateLabels() {
        zoomLabel.textContent = Math.round(scale * 100) + "%";
        pageLabel.textContent = pageNum + " / " + pageCount;
        container.querySelector('[data-act="prev"]').disabled = (pageNum <= 1);
        container.querySelector('[data-act="next"]').disabled = (pageNum >= pageCount);
      }
  
      function fitToWidth(page) {
        const avail = wrap.clientWidth - 2;
        const viewport1 = page.getViewport({ scale: 1 });
        baseScale = avail / viewport1.width;
        scale = baseScale;
      }
  
      async function renderPage() {
        if (rendering) return;
        rendering = true;
        const page = await pdfDoc.getPage(pageNum);
        if (baseScale === 1) fitToWidth(page);
        const viewport = page.getViewport({ scale });
        canvas.style.width = Math.round(viewport.width) + "px";
        canvas.style.height = Math.round(viewport.height) + "px";
        canvas.width = Math.round(viewport.width * dpr);
        canvas.height = Math.round(viewport.height * dpr);
        const transform = dpr !== 1 ? [dpr,0,0,dpr,0,0] : null;
        await page.render({ canvasContext: ctx, viewport, transform }).promise;
        rendering = false;
        updateLabels();
      }
  
      async function start() {
        pdfDoc = await pdfjsLib.getDocument(url).promise;
        pageCount = pdfDoc.numPages;
        pageNum = 1;
        await renderPage();
        if ("ResizeObserver" in window) {
          const ro = new ResizeObserver(() => { baseScale = 1; renderPage(); });
          ro.observe(container);
        } else {
          window.addEventListener("resize", () => { baseScale = 1; renderPage(); });
        }
      }
  
      // buttons
      container.addEventListener("click", (e) => {
        const act = e.target.dataset.act;
        if (!act) return;
        if (act === "zoomIn")  { scale = Math.min(scale + 0.15, 4); renderPage(); }
        if (act === "zoomOut") { scale = Math.max(scale - 0.15, 0.4); renderPage(); }
        if (act === "fit")     { baseScale = 1; renderPage(); }
        if (act === "prev" && pageNum > 1)            { pageNum--; renderPage(); }
        if (act === "next" && pageNum < pageCount)    { pageNum++; renderPage(); }
      });
  
      await new Promise((resolve) => ensurePdfJs(resolve));
      setWorker();
      start();
    }
  
    // Auto-init all elements with data-pdf-url
    function autoInit() {
      document.querySelectorAll("[data-pdf-url]").forEach((el) => {
        const url = el.getAttribute("data-pdf-url");
        if (!url) return;
        mountPdfViewer(el, url);
      });
    }
  
    // Expose manual API + auto-init
    window.initPdfViewer = mountPdfViewer;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", autoInit);
    } else {
      autoInit();
    }
  })();
  