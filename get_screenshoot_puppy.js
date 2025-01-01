const puppeteer = require('puppeteer');
const sharp = require('sharp');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox'],
    headless: false
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
  
  await page.goto(url, {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForSelector('body', {
    timeout: 60000
  });
  
  // Прокручиваем страницу вниз на 2 экрана и возвращаемся вверх
  for (let i = 0; i < 2; i++) {
    await page.evaluate(() => window.scrollBy(0, window.innerHeight));
    await new Promise(resolve => setTimeout(resolve, 1000)); // Пауза для загрузки контента
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  
  // Дополнительное время для завершения загрузки
  await new Promise(resolve => setTimeout(resolve, 3000));
  
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
  
  // Создаем скриншот и сохраняем в папку screenshoots
  const screenshotPath = `screenshoots/${screenshotName}.png`;
  await page.screenshot({ 
    path: screenshotPath,
    clip: {
      x: 0,
      y: 0,
      width: viewportWidth,
      height: viewportHeight
    }
  });
  
  // Настройки обработки изображения
  const webpQuality = 80;
  const scaleFactor = 0.5; // Масштаб 50%
  
  // Конвертируем в WebP с уменьшением размера
  const webpPath = `screenshoots/${screenshotName}.webp`;
  await sharp(screenshotPath)
    .resize({
      width: Math.round(viewportWidth * scaleFactor),
      height: Math.round(viewportHeight * scaleFactor),
      fit: 'inside',
      withoutEnlargement: true
    })
    .webp({ quality: webpQuality })
    .toFile(webpPath)
    .catch(err => {
      console.error('Error converting to WebP:', err);
    });
  
  console.log(`Screenshots saved:
  - Original PNG: ${screenshotPath}
  - Compressed WebP: ${webpPath}`);
  
  await browser.close();
})();
