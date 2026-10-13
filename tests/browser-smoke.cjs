// End-to-end test of the real Pyodide runtime using the locally served web UI.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({headless: true, args: ["--no-sandbox"]});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (err) => errors.push(String(err)));
    await page.goto("http://127.0.0.1:8765/web/index.html", {waitUntil: "domcontentloaded"});
    await page.waitForFunction(() => !document.querySelector("#submit").disabled, null, {timeout: 120000});
    assert.match(await page.locator("#runtime-status").textContent(), /Python runtime ready/);

    await page.locator("#submit").click();
    const sodium = await page.locator("#results").innerText();
    assert.match(sodium, /na deficit meq/i);
    assert.match(sodium, /210(?:\.0)?/);

    await page.locator("#mode").selectOption("potassium");
    await page.locator("#submit").click();
    const potassium = await page.locator("#results").innerText();
    assert.match(potassium, /moderate/i);
    assert.equal(errors.length, 0, errors.join("\n"));
    console.log("Browser Pyodide sodium and potassium workflows passed.");
  } finally {
    await browser.close();
  }
})().catch(err => { console.error(err); process.exitCode = 1; });
