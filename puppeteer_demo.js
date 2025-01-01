const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox'],
    headless: false
  });
  const page = await browser.newPage();
  
  // Устанавливаем размер viewport в соотношении 3:4
  const viewportWidth = 1281;
  const viewportHeight = 1708;
  await page.setViewport({ width: viewportWidth, height: viewportHeight });
  
  await page.goto('https://dragonswhore-cyoas.neocities.org/Princess_Quest/', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForSelector('body', {
    timeout: 60000
  });
  
  // Прокручиваем страницу вниз на 3 экрана и возвращаемся вверх
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.scrollBy(0, window.innerHeight));
    await new Promise(resolve => setTimeout(resolve, 1000)); // Пауза для загрузки контента
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  
  // Дополнительное время для завершения загрузки
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  // Извлекаем имя для скриншота из URL
  const url = new URL(page.url());
  const pathParts = url.pathname.split('/').filter(Boolean);
  
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
  
  console.log(`Screenshot saved as ${screenshotPath}`);
  
  await browser.close();
})();
