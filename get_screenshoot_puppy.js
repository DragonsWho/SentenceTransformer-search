const puppeteer = require('puppeteer');
const sharp = require('sharp');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox'],
    headless: false,
    protocolTimeout: 300000 // 5 minutes
  });
  const page = await browser.newPage();
  
  // Устанавливаем viewport 3:4 для карточки каталога
  const viewportWidth = 1920;
  const viewportHeight = 2560;
  await page.setViewport({ 
    width: viewportWidth,
    height: viewportHeight,
    deviceScaleFactor: 2
  });
  
  // Get URL from command line arguments
  const url = process.argv[2];
  if (!url) {
    console.error('URL argument is required');
    process.exit(1);
  }
  
  // Navigate to URL with basic wait
  await page.goto(url, {
    waitUntil: 'domcontentloaded',
    timeout: 300000 // 5 minutes
  });

  // Wait for body element
  await page.waitForSelector('body', {
    timeout: 300000 // 5 minutes
  });

  // Screenshot schedule: first after 15s, second after 30s, then every minute for 10 minutes
  const maxAttempts = 12; // 15s, 30s, then 10 minutes
  let validScreenshot = false;
  let attempt = 0;

  // Извлекаем имя для скриншота из URL
  const parsedUrl = new URL(page.url());
  const pathParts = parsedUrl.pathname.split('/').filter(Boolean);
  
  let screenshotName;
  if (pathParts.length > 0) {
    // Если последняя часть - index.html, берем предпоследнюю часть
    if (pathParts[pathParts.length - 1] === 'index.html') {
      screenshotName = pathParts[pathParts.length - 2] || 
                      url.hostname.split('.')[0];
    } else {
      // Иначе берем последнюю часть пути
      screenshotName = pathParts[pathParts.length - 1];
    }
  } else {
    // Если путь пустой, используем имя поддомена
    screenshotName = url.hostname.split('.')[0];
  }

  while (attempt < maxAttempts && !validScreenshot) {
    // Calculate delay based on attempt number
    const delay = attempt === 0 ? 15000 : // 15s for first attempt
                  attempt === 1 ? 30000 : // 30s for second attempt
                  60000; // 1 minute for subsequent attempts
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Perform full scroll cycle
    for (let i = 0; i < 2; i++) {
      await page.evaluate(() => window.scrollBy(0, window.innerHeight));
      await new Promise(resolve => setTimeout(resolve, 1000)); // Pause for content loading
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await new Promise(resolve => setTimeout(resolve, 3000)); // Final rendering delay
    // Create and convert screenshot
    const screenshotPath = `screenshoots/${screenshotName}.png`;
    const webpPath = `screenshoots/${screenshotName}.webp`;
    
    await page.screenshot({ 
      path: screenshotPath,
      clip: {
        x: 0,
        y: 0,
        width: viewportWidth,
        height: viewportHeight
      }
    });
    
    // Convert to WebP and check size
    try {
      await sharp(screenshotPath)
        .resize({
          width: Math.round(viewportWidth * 0.5),
          height: Math.round(viewportHeight * 0.5),
          fit: 'inside',
          withoutEnlargement: true
        })
        .webp({ quality: 80 })
        .toFile(webpPath);

      const fs = require('fs');
      const stats = fs.statSync(webpPath);
      const fileSizeInKB = stats.size / 1024;

      if (fileSizeInKB > 10) { // 10KB threshold
        validScreenshot = true;
        console.log(`Valid screenshot captured: ${webpPath} (${fileSizeInKB.toFixed(2)} KB)`);
      } else {
        console.log(`Screenshot too small (${fileSizeInKB.toFixed(2)} KB), retrying...`);
      }
    } catch (err) {
      console.error('Error checking screenshot size:', err);
    }

    attempt++;
  }

  if (!validScreenshot) {
    throw new Error('Failed to capture valid screenshot after maximum attempts');
  }

  try {
    // Clean up temporary PNG file
    const fs = require('fs');
    fs.unlinkSync(`screenshoots/${screenshotName}.png`);
  } catch (err) {
    console.error('Error cleaning up temporary file:', err);
  } finally {
    await browser.close();
  }
})();
