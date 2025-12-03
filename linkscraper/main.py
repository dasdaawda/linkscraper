import argparse
from pathlib import Path

from linkscraper.config import ScraperConfig
from linkscraper.scrapers.linkedin_invitations import LinkedInInvitationsScraper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LinkedIn Invitations Scraper")
    parser.add_argument(
        "--user-data-dir",
        type=str,
        default=None,
        help="Path to existing browser user data directory for authenticated session"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="output.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--output-xlsx",
        type=str,
        default="output.xlsx",
        help="Path to output XLSX file"
    )
    parser.add_argument(
        "--resume-state",
        type=str,
        default="data/state.json",
        help="Path to resume state JSON file"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--target-url",
        type=str,
        default="https://www.linkedin.com/mynetwork/invitation-manager/sent/ORGANIZATION/",
        help="Override default target URL"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    config = ScraperConfig(
        target_url=args.target_url,
        output_csv=Path(args.output_csv),
        output_xlsx=Path(args.output_xlsx),
        resume_state_file=Path(args.resume_state),
        headless=args.headless,
        user_data_dir=Path(args.user_data_dir) if args.user_data_dir else None,
    )
    
    scraper = LinkedInInvitationsScraper(config)
    scraper.run()


if __name__ == "__main__":
    main()
