from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssetConfig:
    tenant_id: str
    site_id: str
    asset_id: str
    asset_type: str
    domain: str


@dataclass(frozen=True)
class GeneratorConfig:
    raw: dict[str, Any]
    assets: tuple[AssetConfig, ...]

    @property
    def schema_version(self) -> str:
        return str(self.raw["schema"]["schema_version"])

    @property
    def cadence_seconds(self) -> float:
        return float(self.raw["generation"]["cadence_seconds"])

    @property
    def duration_seconds(self) -> float:
        return float(self.raw["generation"]["duration_seconds"])

    @property
    def anomaly_rate(self) -> float:
        return float(self.raw["generation"]["anomaly_rate"])

    @property
    def seed(self) -> int:
        return int(self.raw["generation"]["seed"])


def load_config(path: str | Path) -> GeneratorConfig:
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    assets: list[AssetConfig] = []
    seen: set[tuple[str, str, str]] = set()
    for tenant in raw.get("tenants", []):
        tenant_id = tenant["tenant_id"]
        for site in tenant.get("sites", []):
            site_id = site["site_id"]
            for asset in site.get("assets", []):
                count = int(asset.get("count", 1))
                if count <= 0:
                    raise ValueError("Asset group count must be positive")
                pattern = asset.get("asset_id_pattern")
                if count > 1 and not pattern:
                    raise ValueError("asset_id_pattern is required when count is greater than one")

                for index in range(1, count + 1):
                    asset_id = pattern.format(index=index) if pattern else asset["asset_id"]
                    key = (tenant_id, site_id, asset_id)
                    if key in seen:
                        raise ValueError(f"Duplicate asset identity: {key}")
                    seen.add(key)
                    assets.append(
                        AssetConfig(
                            tenant_id=tenant_id,
                            site_id=site_id,
                            asset_id=asset_id,
                            asset_type=asset["asset_type"],
                            domain=asset["domain"],
                        )
                    )

    if not assets:
        raise ValueError("Configuration must contain at least one asset")
    if float(raw["generation"]["cadence_seconds"]) <= 0:
        raise ValueError("cadence_seconds must be positive")
    anomaly_rate = float(raw["generation"]["anomaly_rate"])
    if not 0 <= anomaly_rate <= 1:
        raise ValueError("anomaly_rate must be between 0 and 1")

    return GeneratorConfig(raw=raw, assets=tuple(assets))
