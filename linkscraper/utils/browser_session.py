import random
import time
from typing import List, Optional, Tuple

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


class BrowserSession:
    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        user_agents: Optional[List[str]] = None,
        scroll_pause_range: Tuple[float, float] = (1.0, 3.0),
        freeze_chance: float = 0.25,
        freeze_duration_range: Tuple[float, float] = (2.0, 4.0),
        click_delay_range: Tuple[float, float] = (0.5, 1.5),
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.user_agents = user_agents or [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        self.scroll_pause_range = scroll_pause_range
        self.freeze_chance = freeze_chance
        self.freeze_duration_range = freeze_duration_range
        self.click_delay_range = click_delay_range

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        self.playwright = sync_playwright().start()
        user_agent = random.choice(self.user_agents)

        if self.user_data_dir:
            self.context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                user_agent=user_agent,
            )
        else:
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(user_agent=user_agent)

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        return self.page

    def stop(self):
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        finally:
            if self.playwright:
                self.playwright.stop()

    def random_delay(self, min_sec: Optional[float] = None, max_sec: Optional[float] = None):
        min_value = min_sec if min_sec is not None else self.click_delay_range[0]
        max_value = max_sec if max_sec is not None else self.click_delay_range[1]
        time.sleep(random.uniform(min_value, max_value))

    def human_like_scroll(self, page: Page, scroll_amount: int = 400):
        jitter = random.randint(-100, 100)
        page.mouse.wheel(0, max(200, scroll_amount + jitter))
        self.random_delay(*self.scroll_pause_range)

        if random.random() < self.freeze_chance:
            freeze_time = random.uniform(*self.freeze_duration_range)
            time.sleep(freeze_time)

    def scroll_to_bottom(
        self,
        page: Page,
        max_scrolls: int = 1000,
    ) -> int:
        scroll_count = 0
        previous_height = page.evaluate('document.body.scrollHeight')
        stable_scrolls = 0

        while scroll_count < max_scrolls:
            self.human_like_scroll(page)
            scroll_count += 1

            page.wait_for_timeout(int(self.scroll_pause_range[1] * 1000))
            current_height = page.evaluate('document.body.scrollHeight')
            if current_height == previous_height:
                stable_scrolls += 1
                if stable_scrolls >= 3:
                    break
            else:
                stable_scrolls = 0
                previous_height = current_height

        return scroll_count
