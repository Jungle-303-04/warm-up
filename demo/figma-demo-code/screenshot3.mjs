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
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--headless'],
  defaultViewport: { width: 1440, height: 900 },
});

const page = await browser.newPage();
await page.goto('http://localhost:5174', { waitUntil: 'networkidle0', timeout: 20000 });
await new Promise(r => setTimeout(r, 2000));

for (const screen of SCREENS) {
  await page.evaluate((text) => {
    const btns = Array.from(document.querySelectorAll('nav button'));
    const btn = btns.find(b => b.textContent.trim().includes(text));
    if (btn) btn.click();
  }, screen.text);
  await new Promise(r => setTimeout(r, 800));
  const path = `${OUT}/${screen.label}.png`;
  await page.screenshot({ path });
  console.log(`✓ ${screen.label}.png`);
}

await browser.close();
console.log('\nDone →', OUT);
