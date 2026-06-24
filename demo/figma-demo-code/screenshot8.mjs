import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'fs';

const LIBDIR1 = '/tmp/glib-local/glib-extracted/usr/lib/x86_64-linux-gnu';
const LIBDIR2 = '/tmp/glib-local/glib-extracted/lib/x86_64-linux-gnu';
process.env.LD_LIBRARY_PATH = `${LIBDIR1}:${LIBDIR2}`;

const CHROME = '/home/foundry/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell';

const SCREENS = [
  { label: '01_dashboard',      text: 'Dashboard' },
  { label: '02_app_detail',     text: 'App Detail' },
  { label: '03_resource_graph', text: 'Resource Graph' },
  { label: '04_git_diff',       text: 'Git Diff' },
  { label: '05_evidence',       text: 'Evidence' },
  { label: '06_ai_analysis',    text: 'AI Analysis' },
  { label: '07_pr_recovery',    text: 'PR / Recovery' },
];

const OUT = '/workspaces/default/code/screenshots';
mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--headless'],
  defaultViewport: { width: 1440, height: 900, deviceScaleFactor: 1 },
});

const page = await browser.newPage();

await page.setRequestInterception(true);
page.on('request', req => {
  if (req.url().includes('fonts.g')) req.abort();
  else req.continue();
});

// Inject before page load - force strong contrast + zoom
await page.evaluateOnNewDocument(() => {
  const observe = () => {
    if (!document.head) { requestAnimationFrame(observe); return; }
    const s = document.createElement('style');
    // Boost all text to be clearly visible + scale up the UI
    s.textContent = `
      html { zoom: 1.45 !important; }
      * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
      }
      /* Override all light text colors to be clearly readable */
      span, div, p, button, a, td, th, label, code, pre {
        color: inherit;
      }
      /* Ensure muted text is still dark enough to read */
      .text-slate-300, .text-slate-200, .text-slate-100 { color: #9ca3af !important; }
      .text-slate-400 { color: #6b7280 !important; }
      .text-slate-500 { color: #4b5563 !important; }
      .text-slate-600 { color: #374151 !important; }
      .text-slate-700 { color: #1f2937 !important; }
      /* Fix Tailwind's color overrides for inline-style muted colors */
    `;
    document.head.appendChild(s);
  };
  observe();
});

await page.goto('http://localhost:5175', { waitUntil: 'networkidle0', timeout: 30000 });

// Post-load: walk all elements and darken very light text colors
await page.evaluate(() => {
  // Also force all inline style colors that are too light
  document.querySelectorAll('*').forEach(el => {
    const color = window.getComputedStyle(el).color;
    // Parse rgba
    const m = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (m) {
      const [r, g, b] = [+m[1], +m[2], +m[3]];
      const luminance = (0.299*r + 0.587*g + 0.114*b);
      // If very light (>210 on white bg), darken it
      if (luminance > 210 && el.textContent.trim()) {
        el.style.setProperty('color', '#64748b', 'important');
      }
    }
  });
});

await new Promise(r => setTimeout(r, 1200));

for (const screen of SCREENS) {
  await page.evaluate((text) => {
    const btns = Array.from(document.querySelectorAll('aside button, nav button'));
    const btn = btns.find(b => b.textContent.trim().includes(text));
    if (btn) btn.click();
  }, screen.text);

  await new Promise(r => setTimeout(r, 800));

  await page.screenshot({ path: `${OUT}/${screen.label}.png` });
  console.log(`✓ ${screen.label}.png`);
}

await browser.close();
console.log('\nDone →', OUT);
