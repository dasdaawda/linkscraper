import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ScraperConfig:
    target_url: str = "https://www.linkedin.com/mynetwork/invitation-manager/sent/ORGANIZATION/"
    output_csv: Path = Path("output.csv")
    output_xlsx: Path = Path("output.xlsx")
    resume_state_file: Path = Path("data/state.json")
    logs_dir: Path = Path("logs")
    headless: bool = False
    user_data_dir: Optional[Path] = None
    scroll_pause_range: Tuple[float, float] = (1.0, 3.0)
    click_delay_range: Tuple[float, float] = (0.5, 1.5)
    freeze_chance: float = 0.25
    freeze_duration_range: Tuple[float, float] = (2.0, 4.0)
    progress_interval: int = 5
    max_scrolls_without_new_content: int = 5
    scroll_batch_size: int = 3
    output_encoding: str = "utf-8"
    max_resume_entries: Optional[int] = 5000
    max_html_snippet_length: int = 500
    user_agents: Optional[List[str]] = field(default=None)

    def __post_init__(self):
        if isinstance(self.output_csv, str):
            self.output_csv = Path(self.output_csv)
        if isinstance(self.output_xlsx, str):
            self.output_xlsx = Path(self.output_xlsx)
        if isinstance(self.resume_state_file, str):
            self.resume_state_file = Path(self.resume_state_file)
        if isinstance(self.logs_dir, str):
            self.logs_dir = Path(self.logs_dir)

        if self.user_data_dir is None:
            env_profile = os.environ.get("LINKEDIN_USER_DATA_DIR")
            if env_profile:
                self.user_data_dir = Path(env_profile).expanduser()
        elif isinstance(self.user_data_dir, str):
            self.user_data_dir = Path(self.user_data_dir)

        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            ]

    @property
    def scraper_log_file(self) -> Path:
        return self.logs_dir / "scraper.log"

    @property
    def unparsed_log_file(self) -> Path:
        return self.logs_dir / "unparsed_items.log"
