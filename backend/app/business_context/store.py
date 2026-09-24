from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import BusinessContextProfile
from .serialization import business_context_profile_from_dict


class ProfileNotFoundError(KeyError):
    pass


class JsonBusinessContextProfileStore:
    """Simple application-configuration persistence for the MVP.

    This intentionally avoids adding PostgreSQL tables before the profile model
    has been reviewed. Each profile is data/configuration, not Python mapping logic.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, profile_id: str) -> Path:
        safe = profile_id.strip()
        if not safe or any(part in safe for part in ("/", "\\", "..")):
            raise ValueError("profile_id contains unsupported path characters")
        return self.root / f"{safe}.json"

    def save(self, profile: BusinessContextProfile) -> BusinessContextProfile:
        target = self._path_for(profile.profile_id)
        payload = json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.root,
            delete=False,
            suffix=".tmp",
        ) as temp:
            temp.write(payload)
            temp_path = Path(temp.name)

        temp_path.replace(target)
        return profile

    def get(self, profile_id: str) -> BusinessContextProfile:
        path = self._path_for(profile_id)
        if not path.exists():
            raise ProfileNotFoundError(profile_id)
        return business_context_profile_from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )

    def list_profiles(self) -> list[BusinessContextProfile]:
        return [
            business_context_profile_from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
            for path in sorted(self.root.glob("*.json"), key=lambda p: p.name)
        ]
