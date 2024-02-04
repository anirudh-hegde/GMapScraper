# This script serves as an example of how to use Python
# & Playwright to scrape/extract data from Google Maps

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials


@dataclass
class Business:
    """Holds business data"""

    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    latitude: float = None
    longitude: float = None
    category: str = None
    reviews_count: int = None
    reviews_average: float = None


@dataclass
class BusinessList:

    business_list: list[Business] = field(default_factory=list)
    save_at = 'output'


    def dataframe(self):

        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):

        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"output/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):


        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/{filename}.csv", index=False)


def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    """Helper function to extract coordinates from URL"""

    coordinates = url.split('/@')[-1].split('/')[0]
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])


def main():
    # Read search from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    if args.search:
        search_list = [args.search]

    if args.total:
        total = args.total
    else:
        # If there is no total is passed  we will set the value to a random latge number
        total = 1_000_000

    if not args.search:
        #########
        # input #
        #########
        categories = ["restaurant", "hotel", "pharmacy", "gym", "bank"]
        search_list = categories

    # Scraping
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Loop through specified categories
        for search_for_index, search_for in enumerate(search_list):
            print(f"-----\n{search_for_index} - {search_for}".strip())
            page.goto("https://www.google.com/maps", timeout=60000)
            page.wait_for_timeout(5000)

            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.wait_for_timeout(3000)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # Scrolling📜
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')


            previously_counted = 0
            index = 0
            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(3000)

                if (
                        page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        >= total
                ):
                    listings = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()[:total]
                    listings = [listing.locator("xpath=..") for listing in listings]
                    print(f"Total Scraped: {len(listings)}")
                    break
                else:

                    if (
                            page.locator(
                                '//a[contains(@href, "https://www.google.com/maps/place")]'
                            ).count()
                            == previously_counted
                    ):
                        listings = page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).all()
                        print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                        break
                    else:
                        previously_counted = page.locator(
                            '//a[contains(@href, "https://www.google.com/maps/place")]'
                        ).count()
                        print(
                            f"Currently Scraped: ",
                            page.locator(
                                '//a[contains(@href, "https://www.google.com/maps/place")]'
                            ).count(),
                        )

            business_list = BusinessList()

            # Scraping
            for listing in listings:
                index += 1
                try:
                    listing.click()
                    page.wait_for_timeout(5000)

                    name_xpath = f'(//div[contains(@class, "qBF1Pd fontHeadlineSmall ")])[{index + 1}]'
                    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    category_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button'
                    reviews_span_xpath = '//span[@aria-hidden="true"]/text()'

                    # reviews_span_xpath = f'(//div[contains(@class, "F7nice")])[{index + 1}]//span[@aria-hidden="true"]'
                    # reviews_span_xpath = '//div[contains(@class, "section-review-content")]'
                    #

                    # reviews_span_xpath = "//div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]"
                    # reviews_span_xpath = '//span[contains(@class, "section-rating")]/span[contains(@class, "section-star-display")] | /html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]'
                    # reviews_span_xpath = f'(//div[contains(@class, "F7nice")])[{index + 1}]'

                    # name_xpath = '//div[contains(@class, "fontHeadlineSmall")]'
                    # name_xpath = '//h1[@data-section-id="title"]'
                    # address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    # website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    # phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    # reviews_span_xpath = '//span[@role="img"]'

                    # name_xpath = '//h1[@data-section-id="title"]'
                    # reviews_count_xpath = '//button[contains(@aria-label, "reviews")]/span[contains(@class, "gm2-caption")]'

                    # name_xpath = '//div[contains(@class, "fontHeadlineSmall")]'
                    # address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    # website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    # phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    # reviews_span_xpath = '//span[@role="img"]'
                    # reviews_count_xpath = '//button[contains(@aria-label, "reviews")]/span[contains(@class, "gm2-caption")]'

                    business = Business()

                    # if page.locator(name_xpath).count() > 0:
                    #     business.name = page.locator(name_xpath).all()[0].inner_text()
                    # else:
                    #     business.name = ""

                    if page.locator(name_xpath).count() > 0:
                        business.name = page.locator(name_xpath).all()[0].inner_text()
                        print(f"Extracted name: {business.name}")
                    else:
                        business.name = ""
                    if page.locator(address_xpath).count() > 0:
                        business.address = page.locator(address_xpath).all()[0].inner_text()
                    else:
                        business.address = ""
                    if page.locator(website_xpath).count() > 0:
                        business.website = page.locator(website_xpath).all()[0].inner_text()
                    else:
                        business.website = ""
                    if page.locator(phone_number_xpath).count() > 0:
                        business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                    else:
                        business.phone_number = ""
                    # if page.locator(reviews_count_xpath).count() > 0:
                    #     reviews_count_text = page.locator(reviews_count_xpath).all()[0].inner_text().strip()
                    #     business.reviews_count = int(reviews_count_text.replace(',', ''))
                    # else:
                    #     business.reviews_count = 0

                    if listing.locator(reviews_span_xpath).count() > 0:
                        business.reviews_average = float(
                            listing.locator(reviews_span_xpath)
                            .locator('span[aria-hidden="true"]')
                            .inner_text()
                        )
                        business.reviews_count = int(
                            listing.locator(reviews_span_xpath)
                            .locator('span[aria-label*="reviews"]')
                            .inner_text()
                            .split()[0]
                            .replace(',', '')
                        )
                    else:
                        business.reviews_average = ""
                        business.reviews_count = ""

                    business.latitude, business.longitude = extract_coordinates_from_url(page.url)

                    # Extract additional GMB details
                    # try:
                    #     hours_xpath = '//*[@class="section-open-hours-container"]'
                    #     if page.locator(hours_xpath).count() > 0:
                    #         business.hours = page.locator(hours_xpath).all()[0].inner_text()
                    # except Exception as e:
                    #     print(f'Error extracting hours: {e}')

                    business.category = search_for  # Set the category

                    business_list.business_list.append(business)
                except Exception as e:
                    print(f'Error occurred: {e}')

            # Output
            business_list.save_to_excel(f"google_maps_data_{search_for}".replace(' ', '_'))
            business_list.save_to_csv(f"google_maps_data_{search_for}".replace(' ', '_'))

        browser.close()


if __name__ == "__main__":
    main()
