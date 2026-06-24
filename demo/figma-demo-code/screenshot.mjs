import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const SCREENS = [
  { id: 'dashboard',      label: '01_dashboard' },
  { id: 'detail',         label: '02_app_detail' },
  { id: 'resource-graph', label: '03_resource_graph' },
  { id: 'git-diff',       label: '04_git_diff' },
  { id: 'evidence',       label: '05_evidence' },
  { id: 'ai-analysis',    label: '06_ai_analysis' },
  { id: 'pr-recovery',    label: '07_pr_recovery' },
];

const OUT_DIR = '/workspaces/default/code/screenshots';
mkdirSync(OUT_DIR, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setViewportSize({ width: 1440, height: 900 });

// Load the app
await page.goto('http://localhost:5174', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

for (const screen of SCREENS) {
  // Click the nav item in the sidebar
  // Find button by text content
  const navBtn = page.locator(`nav button`).filter({ hasText: screen.id === 'dashboard' ? 'Dashboard'
    : screen.id === 'detail'         ? 'App Detail'
    : screen.id === 'resource-graph' ? 'Resource Graph'
    : screen.id === 'git-diff'       ? 'Git Diff'
    : screen.id === 'evidence'       ? 'Evidence'
    : screen.id === 'ai-analysis'    ? 'AI Analysis'
    : 'PR / Recovery'
  });
  await navBtn.click();
  await page.waitForTimeout(800);

  const path = `${OUT_DIR}/${screen.label}.png`;
  await page.screenshot({ path, fullPage: false });
  console.log(`✓ ${path}`);
}

await browser.close();
console.log('\nDone! Screenshots saved to', OUT_DIR);
