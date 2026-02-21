const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const seeds = [84,85,86,87,88,89,90,91,92,93];
  let grandTotal = 0;
  
  for (const seed of seeds) {
    console.log(`Processing seed ${seed}...`);
    
    await page.goto(`https://sanand0.github.io/tdsdata/js_table/?seed=${seed}`);
    
    // Wait for tables to fully load (adjust selector if needed)
    await page.waitForSelector('table', { timeout: 5000 });
    
    // Get ALL table cells on page (covers all tables)
    const cells = await page.locator('td').all();
    
    let pageSum = 0;
    for (const cell of cells) {
      const text = await cell.textContent();
      const num = parseFloat(text);
      if (!isNaN(num)) {
        pageSum += num;
      }
    }
    
    console.log(`Seed ${seed} sum: ${pageSum}`);
    grandTotal += pageSum;
  }
  
  console.log(`\nGRAND TOTAL: ${grandTotal}`);
  await browser.close();
})();
