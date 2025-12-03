import time
from dataclasses import dataclass, asdict
from typing import List, Optional

import pandas as pd
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from linkscraper.config import ScraperConfig
from linkscraper.utils.browser_session import BrowserSession
from linkscraper.utils.deduplicator import Deduplicator
from linkscraper.utils.logger import ScraperLogger


@dataclass
class InvitationEntry:
    profile_name: str
    profile_url: str
    invitation_date: str
    invited_to: str


class LinkedInInvitationsScraper:
    CARD_SELECTORS = [
        "li.invitation-card",
        "div[data-test-invitation-card]",
        "li[data-chameleon-result-urn]",
        "li.scaffold-finite-scroll__content li",
    ]
    CARD_SELECTOR = ", ".join(CARD_SELECTORS)

    NAME_SELECTORS = [
        '.invitation-card__name',
        '.artdeco-entity-lockup__title',
        '.artdeco-entity-lockup__subtitle',
        '.entity-result__title-text',
        '[class*="name"]',
    ]

    DATE_SELECTORS = [
        '.invitation-card__date',
        'time',
        '[class*="time"]',
    ]

    INVITED_TO_SELECTORS = [
        '.invitation-card__subtitle',
        '[class*="subtitle"]',
    ]

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.logger = ScraperLogger(log_dir=str(config.logs_dir))
        self.browser_session = BrowserSession(
            headless=config.headless,
            user_data_dir=str(config.user_data_dir) if config.user_data_dir else None,
            user_agents=config.user_agents,
            scroll_pause_range=config.scroll_pause_range,
            freeze_chance=config.freeze_chance,
            freeze_duration_range=config.freeze_duration_range,
            click_delay_range=config.click_delay_range,
        )
        self.deduplicator = Deduplicator(
            state_file=config.resume_state_file,
            max_entries=config.max_resume_entries,
        )
        self.entries: List[InvitationEntry] = []
        self.total_cards_seen = 0
        self.duplicates_found = 0
        self.processed_dom_cards = 0

    def run(self):
        try:
            self.logger.log_start(self.config.target_url)
            self.deduplicator.load_state()

            if not self.config.user_data_dir:
                self.logger.log_warning(
                    "User data directory is not specified. Authenticated session may not be available."
                )

            page = self.browser_session.start()
            self.logger.log_progress("Browser session started")

            self.logger.log_progress(f"Navigating to {self.config.target_url}")
            page.goto(self.config.target_url, wait_until='networkidle', timeout=60000)
            self.browser_session.random_delay(2, 4)

            self._wait_for_page_load(page)

            initial_dom_count = self._count_dom_cards(page)
            if initial_dom_count:
                processed = self._extract_invitations_from_page(page, 0, initial_dom_count)
                self.processed_dom_cards = initial_dom_count
                if processed:
                    self.logger.log_progress(f"Collected {processed} invitations from initial viewport")

            self.logger.log_progress("Starting to scroll and collect invitations...")
            scroll_start = time.perf_counter()
            scroll_count = self._scroll_and_collect(page)
            scroll_duration = time.perf_counter() - scroll_start

            self.logger.log_progress(f"Completed scrolling with {scroll_count} scroll actions")
            self.logger.log_progress(f"New entries collected: {len(self.entries)}")

            output_path = self._save_results()
            self.deduplicator.save_state()

            self.logger.set_item_counts(
                total=self.total_cards_seen,
                unique=len(self.entries),
                duplicates=self.duplicates_found,
            )
            self.logger.set_scroll_time(scroll_duration)
            self.logger.log_end(output_path or str(self.config.output_xlsx))

        except Exception as exc:
            self.logger.log_error(f"Fatal error during scraping: {exc}", exc_info=True)
            raise
        finally:
            self.browser_session.stop()
            self.logger.log_progress("Browser session closed")

    def _wait_for_page_load(self, page: Page):
        self.logger.log_debug("Waiting for page to load invitations...")
        try:
            page.wait_for_selector('div[class*="invitation"]', timeout=15000)
            self.logger.log_debug("Invitation elements detected")
        except PlaywrightTimeoutError:
            self.logger.log_warning(
                "Timeout while waiting for invitation elements. Continuing with available content."
            )

    def _scroll_and_collect(self, page: Page) -> int:
        scroll_count = 0
        consecutive_no_new = 0

        while consecutive_no_new < self.config.max_scrolls_without_new_content:
            for _ in range(self.config.scroll_batch_size):
                self.browser_session.human_like_scroll(page, scroll_amount=500)
                scroll_count += 1
                self.logger.increment_scroll()

            total_dom_cards = self._wait_for_new_content(page, self.processed_dom_cards)
            new_entries = 0

            if total_dom_cards > self.processed_dom_cards:
                new_entries = self._extract_invitations_from_page(
                    page,
                    self.processed_dom_cards,
                    total_dom_cards,
                )
                self.processed_dom_cards = total_dom_cards

            if new_entries == 0:
                consecutive_no_new += 1
                self.logger.log_debug(
                    f"No new items found ({consecutive_no_new}/"
                    f"{self.config.max_scrolls_without_new_content})"
                )
            else:
                consecutive_no_new = 0
                self.logger.log_progress(
                    f"Progress: {len(self.entries)} unique invitations collected (+{new_entries})"
                )

            if self.entries and len(self.entries) % self.config.progress_interval == 0:
                self.logger.log_progress(
                    f"Progress update: {len(self.entries)} invitations collected so far"
                )

        self.logger.log_progress(f"Finished scrolling after {scroll_count} scroll interactions")
        return scroll_count

    def _wait_for_new_content(self, page: Page, previous_dom_count: int) -> int:
        try:
            page.wait_for_function(
                "({ selectors, previous }) => selectors.reduce((total, selector) => "
                "total + document.querySelectorAll(selector).length, 0) > previous",
                {"selectors": self.CARD_SELECTORS, "previous": previous_dom_count},
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            pass
        return self._count_dom_cards(page)

    def _count_dom_cards(self, page: Page) -> int:
        try:
            return page.evaluate(
                "selectors => selectors.reduce((total, selector) => "
                "total + document.querySelectorAll(selector).length, 0)",
                self.CARD_SELECTORS,
            )
        except Exception:
            return 0

    def _extract_invitations_from_page(
        self,
        page: Page,
        start_index: int,
        end_index: Optional[int] = None,
    ) -> int:
        invitation_cards = page.query_selector_all(self.CARD_SELECTOR)
        total_cards = len(invitation_cards)
        if not total_cards:
            return 0

        safe_start = min(start_index, total_cards)
        safe_end = min(end_index or total_cards, total_cards)
        if safe_start >= safe_end:
            return 0

        cards_slice = invitation_cards[safe_start:safe_end]
        new_entries = 0

        for card in cards_slice:
            try:
                entry = self._parse_invitation_card(card)
                self.total_cards_seen += 1

                if self.deduplicator.is_duplicate(entry.profile_url):
                    self.duplicates_found += 1
                    continue

                self.entries.append(entry)
                self.deduplicator.add_url(entry.profile_url)
                self._persist_resume_state()
                new_entries += 1

            except ValueError as exc:
                self._log_unparsed_card(card, str(exc))
            except Exception as exc:
                self._log_unparsed_card(card, "Unhandled parsing error", exc)

        return new_entries

    def _parse_invitation_card(self, card) -> InvitationEntry:
        profile_link = card.query_selector('a[href*="/in/"]')
        if not profile_link:
            profile_link = card.query_selector('a.invitation-card__link')
        if not profile_link:
            profile_link = card.query_selector('a[data-control-name*="profile"]')
        if not profile_link:
            raise ValueError("Profile link not found")

        profile_url = profile_link.get_attribute('href')
        if not profile_url:
            raise ValueError("Profile URL attribute missing")
        profile_url = profile_url.strip()
        if profile_url.startswith('/'):
            profile_url = f"https://www.linkedin.com{profile_url}"
        profile_url = profile_url.split('?')[0]

        profile_name = self._extract_text(card, self.NAME_SELECTORS)
        if not profile_name:
            profile_name = profile_link.inner_text().strip() if profile_link else None
        if not profile_name:
            raise ValueError("Profile name not found")

        invitation_date = self._extract_text(card, self.DATE_SELECTORS)
        if not invitation_date:
            invitation_date = self._extract_line_with_keyword(card, 'Sent') or ""

        invited_to = self._extract_text(card, self.INVITED_TO_SELECTORS)
        if not invited_to:
            invited_to = self._extract_line_with_keyword(card, 'Invited to follow') or ""

        return InvitationEntry(
            profile_name=profile_name,
            profile_url=profile_url,
            invitation_date=invitation_date,
            invited_to=invited_to,
        )

    @staticmethod
    def _extract_text(card, selectors: List[str]) -> Optional[str]:
        for selector in selectors:
            element = card.query_selector(selector)
            if not element:
                continue
            try:
                text = element.inner_text().strip()
            except Exception:
                text = None
            if text:
                return text
        return None

    @staticmethod
    def _extract_line_with_keyword(card, keyword: str) -> Optional[str]:
        try:
            content = card.inner_text()
        except Exception:
            return None
        if not content:
            return None
        keyword_lower = keyword.lower()
        for line in content.splitlines():
            cleaned = line.strip()
            if keyword_lower in cleaned.lower():
                return cleaned
        return None

    def _persist_resume_state(self):
        try:
            self.deduplicator.save_state()
        except Exception as exc:
            self.logger.log_warning(f"Failed to persist resume state: {exc}")

    def _log_unparsed_card(self, card, reason: str, exception: Optional[Exception] = None):
        try:
            html = card.inner_html()
        except Exception:
            html = ""
        snippet = html[: self.config.max_html_snippet_length] if html else "N/A"
        details = reason if not exception else f"{reason}: {exception}"
        self.logger.log_unparsed_item(snippet, details, full_html=html)

    def _save_results(self) -> Optional[str]:
        records = [asdict(entry) for entry in self.entries]
        csv_path = self.config.output_csv
        xlsx_path = self.config.output_xlsx

        if csv_path.exists():
            try:
                existing_df = pd.read_csv(csv_path, encoding=self.config.output_encoding)
                if not existing_df.empty:
                    records = existing_df.to_dict('records') + records
            except Exception as exc:
                self.logger.log_warning(f"Failed to read existing CSV: {exc}")

        if not records:
            self.logger.log_warning("No invitations collected. Output files were not updated.")
            return None

        df = pd.DataFrame(records)
        df = df[['profile_name', 'profile_url', 'invitation_date', 'invited_to']]
        df = df.drop_duplicates(subset=['profile_url']).reset_index(drop=True)

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_path, index=False, encoding=self.config.output_encoding)
        self.logger.log_progress(f"CSV file saved: {csv_path}")

        df.to_excel(xlsx_path, index=False, engine='openpyxl')
        self.logger.log_progress(f"XLSX file saved: {xlsx_path}")

        return str(xlsx_path)
