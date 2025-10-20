import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS = [field.name for field in fields(Product)]
BASE_URL = "https://webscraper.io"
HOME_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "./computers/")
PHONES_URL = urljoin(HOME_URL, "./phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "./laptops/")
TABLETS_URL = urljoin(COMPUTERS_URL, "./tablets/")
TOUCH_URL = urljoin(PHONES_URL, "./touch/")


def parse_page(driver: WebDriver, page_url: str) -> list[Product]:
    wait = WebDriverWait(driver, 1)
    driver.get(page_url)

    try:
        button = wait.until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        button.click()
    except TimeoutException:
        pass

    products = []
    captions = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    for caption in captions:
        products.append(
            Product(
                title=caption.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=caption.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(caption.find_element(
                    By.CSS_SELECTOR, "span[itemprop='price']"
                ).text.replace("$", "")),
                rating=int(caption.find_element(
                    By.CSS_SELECTOR, "p[data-rating]"
                ).get_attribute("data-rating")),
                num_of_reviews=int(caption.find_element(
                    By.CSS_SELECTOR, "span[itemprop='reviewCount']"
                ).text),
            )
        )
    return products


def parse_paginated_page(driver: WebDriver, page_url: str) -> list[Product]:
    wait = WebDriverWait(driver, 1)
    driver.get(page_url)

    try:
        button = wait.until(ec.element_to_be_clickable(
            (By.CLASS_NAME, "acceptCookies")
        ))
        button.click()
    except TimeoutException:
        pass

    while True:
        try:
            more_button = WebDriverWait(driver, 1).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
            time.sleep(1.5)
        except TimeoutException:
            break

    products = []
    captions = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    for caption in captions:
        products.append(
            Product(
                title=caption.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=caption.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(caption.find_element(
                    By.CSS_SELECTOR, "h4.price"
                ).text.replace("$", "")),
                rating=int(len(caption.find_elements(
                    By.CSS_SELECTOR, ".ws-icon.ws-icon-star"
                ))),
                num_of_reviews=int(caption.find_element(
                    By.CSS_SELECTOR, "span[itemprop='reviewCount']"
                ).text),
            )
        )
    return products


def make_tuple(product: Product) -> tuple:
    return tuple(
        [
            product.title,
            product.description,
            product.price,
            product.rating,
            product.num_of_reviews,
        ]
    )


def get_all_products(scrape_list: list[tuple]) -> None:
    driver = webdriver.Chrome()
    try:
        for page, file_name, paginated in scrape_list:
            if paginated:
                products = parse_paginated_page(driver, page)
            else:
                products = parse_page(driver, page)

            with open(file_name, "w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                for product in products:
                    writer.writerow(make_tuple(product))
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products(
        [
            (HOME_URL, "home.csv", False),
            (COMPUTERS_URL, "computers.csv", False),
            (PHONES_URL, "phones.csv", False),
            (TABLETS_URL, "tablets.csv", True),
            (TOUCH_URL, "touch.csv", True),
            (LAPTOPS_URL, "laptops.csv", True),
        ]
    )
