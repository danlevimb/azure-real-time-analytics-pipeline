import json
from pathlib import Path

class GeneratedEventLogger:

    def __init__(
        self,
        *,
        output_path: Path,
    ) -> None:

        self.output_path = output_path
        self.output_path.parent.mkdir(parents = True, exist_ok = True,)
        self._file = self.output_path.open("w", encoding="utf-8",)

    def log(
        self,
        event: dict,
    ) -> None:

        json.dump(
            event,
            self._file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        self._file.write("\n")
        self._file.flush()

    def close(self) -> None:

        self._file.close()