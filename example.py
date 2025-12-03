#!/usr/bin/env python3

from pathlib import Path
from linkscraper.config import ScraperConfig
from linkscraper.scrapers.linkedin_invitations import LinkedInInvitationsScraper


def main():
    config = ScraperConfig(
        target_url="https://www.linkedin.com/mynetwork/invitation-manager/sent/ORGANIZATION/",
        output_csv=Path("output.csv"),
        output_xlsx=Path("output.xlsx"),
        resume_state_file=Path("data/state.json"),
        headless=False,
        user_data_dir=Path("./user_data"),
    )
    
    scraper = LinkedInInvitationsScraper(config)
    scraper.run()


if __name__ == "__main__":
    main()
