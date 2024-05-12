import asyncio, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


async def crawling_data(driver, url):
    page = url[-1]
    driver.switch_to.window(driver.current_window_handle)
    driver.execute_script("window.open('');")
    window_handles = driver.window_handles
    driver.switch_to.window(window_handles[-1])
    driver.get(url)
    elements = driver.find_elements(By.TAG_NAME, "a")
    if len(elements) > 0:
        for i in range(1, 11):
            print("Worker " + str(page) + ": number " + str(i))
            await asyncio.sleep(1)


async def main():
    urls = []
    for i in range(1,7):
        urls.append(f"https://vnexpress.net/the-gioi-p{i}")

    driver = webdriver.Chrome()
    task = [asyncio.create_task(crawling_data(driver, url)) for url in urls]
    response = await asyncio.gather(*task)

asyncio.run(main())
