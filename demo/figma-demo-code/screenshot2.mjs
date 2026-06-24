import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'fs';

const SCREENS = [
  { label: '01_dashboard',      navText: 'Dashboard' },
  { label: '02_app_detail',     navText: 'App Detail' },
  { label: '03_resource_graph', navText: 'Resource Graph' },
  { label: '04_git_diff',       navText: 'Git Diff' },
  { label: '05_evidence',       navText: 'Evidence' },
  { label: '06_ai_analysis',    navText: 'AI Analysis' },
  { label: '07_pr_recovery',    navText: 'PR / Recovery' },
];

const OUT = '/workspaces/default/code/screenshots';
mkdirSync(OUT, { recursive: true });

const execPath = await chromium.executablePath();
console.log('Chrome path:', execPath);

const browser = await puppeteer.launch({
  args: chromium.args,
  defaultViewport: { width: 1440, height: 900 },
  executablePath: execPath,
  headless: true,
});

const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
await page.goto('http://localhost:5174', { waitUntil: 'networkidle0', timeout: 15000 });
await new Promise(r => setTimeout(r, 2000));

for (const screen of SCREENS) {
  // Click nav button matching text
  await page.evaluate((text) => {
    const btns = Array.from(document.querySelectorAll('nav button'));
    const btn = btns.find(b => b.textContent.trim().includes(text));
    if (btn) btn.click();
  }, screen.navText);

  await new Promise(r => setTimeout(r, 700));
  await page.screenshot({ path: `${OUT}/${screen.label}.png` });
  console.log(`✓ ${screen.label}.png`);
}

await browser.close();
console.log('\nAll done →', OUT);
