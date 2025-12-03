import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ScraperLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.main_logger = self._setup_logger(
            "scraper",
            self.log_dir / "scraper.log"
        )
        self.unparsed_logger = self._setup_logger(
            "unparsed",
            self.log_dir / "unparsed_items.log",
            console_output=False
        )
        
        self.start_time: Optional[datetime] = None
        self.total_items = 0
        self.unique_items = 0
        self.duplicates = 0
        self.scroll_count = 0
        self.parsing_errors = 0
        self.scroll_time: Optional[float] = None
    
    def _setup_logger(self, name: str, log_file: Path, console_output: bool = True) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_start(self, url: str):
        self.start_time = datetime.now()
        self.main_logger.info("=" * 80)
        self.main_logger.info("LinkedIn Invitations Scraper Started")
        self.main_logger.info("=" * 80)
        self.main_logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.main_logger.info(f"Target URL: {url}")
        self.main_logger.info("-" * 80)
    
    def log_end(self, output_file: str):
        if not self.start_time:
            self.main_logger.warning("log_end called without log_start")
            return
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        self.main_logger.info("-" * 80)
        self.main_logger.info("Scraping Completed")
        self.main_logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.main_logger.info(f"Total duration: {duration}")
        self.main_logger.info("")
        self.main_logger.info("Statistics:")
        self.main_logger.info(f"  Total items collected: {self.total_items}")
        self.main_logger.info(f"  Unique items: {self.unique_items}")
        self.main_logger.info(f"  Duplicates: {self.duplicates}")
        self.main_logger.info(f"  Page scrolls: {self.scroll_count}")
        if self.scroll_time is not None:
            self.main_logger.info(f"  Scroll duration: {self.scroll_time:.2f}s")
        self.main_logger.info(f"  Parsing errors: {self.parsing_errors}")
        self.main_logger.info(f"  Output file: {output_file}")
        self.main_logger.info("=" * 80)
    
    def log_progress(self, message: str):
        self.main_logger.info(message)
    
    def log_error(self, message: str, exc_info: bool = False):
        self.main_logger.error(message, exc_info=exc_info)
    
    def log_warning(self, message: str):
        self.main_logger.warning(message)
    
    def log_debug(self, message: str):
        self.main_logger.debug(message)
    
    def log_unparsed_item(self, html_snippet: str, reason: str, full_html: str = None):
        self.parsing_errors += 1
        self.unparsed_logger.error("-" * 80)
        self.unparsed_logger.error(f"Parsing Error #{self.parsing_errors}")
        self.unparsed_logger.error(f"Reason: {reason}")
        self.unparsed_logger.error(f"HTML snippet (first 500 chars):")
        self.unparsed_logger.error(html_snippet[:500])
        if full_html:
            self.unparsed_logger.error(f"Full HTML:")
            self.unparsed_logger.error(full_html[:2000])
        self.unparsed_logger.error("-" * 80)
    
    def increment_scroll(self):
        self.scroll_count += 1
    
    def set_item_counts(self, total: int, unique: int, duplicates: int):
        self.total_items = total
        self.unique_items = unique
        self.duplicates = duplicates
    
    def set_scroll_time(self, time_seconds: float):
        self.scroll_time = time_seconds
