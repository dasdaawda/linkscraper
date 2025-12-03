import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class Deduplicator:
    state_file: Path
    max_entries: Optional[int] = None
    seen_urls: Set[str] = field(default_factory=set)
    ordered_urls: List[str] = field(default_factory=list)
    last_processed_url: Optional[str] = None

    def load_state(self) -> None:
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            self.seen_urls = set()
            self.ordered_urls = []
            self.last_processed_url = None
            return

        urls = data.get('seen_urls', [])
        self.seen_urls = set(urls)
        self.ordered_urls = list(urls)
        metadata = data.get('metadata', {})
        self.last_processed_url = metadata.get('last_processed_url')

    def save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        urls = self.ordered_urls

        if self.max_entries and len(urls) > self.max_entries:
            urls = urls[-self.max_entries:]
            self.ordered_urls = list(urls)
            self.seen_urls = set(urls)

        payload = {
            'seen_urls': urls,
            'metadata': {
                'last_processed_url': self.last_processed_url,
                'updated_at': datetime.utcnow().isoformat(),
            },
        }

        with open(self.state_file, 'w', encoding='utf-8') as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def is_duplicate(self, url: str) -> bool:
        return url in self.seen_urls

    def add_url(self, url: str) -> None:
        if url not in self.seen_urls:
            self.seen_urls.add(url)
            self.ordered_urls.append(url)
        self.last_processed_url = url

    def add_urls(self, urls: List[str]) -> None:
        for url in urls:
            self.add_url(url)
