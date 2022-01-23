from typing import Optional

from rich.progress import ProgressColumn
from rich.table import Column
from rich.text import Text


class OptimizeImageColumn(ProgressColumn):
    """Renders images optimizer and total, e.g. '2/8 images'."""

    def __init__(self, table_column: Optional[Column] = None) -> None:
        super().__init__(table_column=table_column)

    def render(self, task: "Task") -> Text:
        """Calculate common unit for completed and total."""
        completed = int(task.completed)
        total = int(task.total)
        download_status = f"{completed}/{total} images"
        download_text = Text(download_status, style="progress.download")
        return download_text
