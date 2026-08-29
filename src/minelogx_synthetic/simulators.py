from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import AssetConfig
from .events import build_event


@dataclass
class AssetState:
    sequence_no: int = 0
    engine_hours: float = 8452.60
    odometer_km: float = 412934.27
    total_fuel_litres: float = 185492.38
    fuel_level_pct: float = 72.0
    health_index: float = 1.0
    latitude: float = -16.590400
    longitude: float = -71.537500
    cycle_index: int = 1
    cycle_step: int = 0


class Simulator:
    def __init__(
        self,
        asset: AssetConfig,
        schema_version: str,
        anomaly_rate: float,
        rng: random.Random,
    ) -> None:
        self.asset = asset
        self.schema_version = schema_version
        self.anomaly_rate = anomaly_rate
        self.rng = rng
        self.state = AssetState(
            engine_hours=rng.uniform(800, 22_000),
            odometer_km=rng.uniform(20_000, 650_000),
            total_fuel_litres=rng.uniform(10_000, 450_000),
            fuel_level_pct=rng.uniform(25, 95),
            latitude=-16.590400 + rng.uniform(-0.08, 0.08),
            longitude=-71.537500 + rng.uniform(-0.08, 0.08),
        )

    def next_event(self, timestamp: datetime, elapsed_seconds: float) -> dict[str, Any]:
        self.state.sequence_no += 1
        measurements = self._measurements(elapsed_seconds)
        return build_event(
            asset=self.asset,
            schema_version=self.schema_version,
            timestamp=timestamp,
            sequence_no=self.state.sequence_no,
            measurements=measurements,
        )

    def _measurements(self, elapsed_seconds: float) -> dict[str, Any]:
        raise NotImplementedError


class FleetSimulator(Simulator):
    _cycle_states = ("loading", "hauling", "dumping", "returning")

    def _measurements(self, elapsed_seconds: float) -> dict[str, Any]:
        state = self._cycle_states[self.state.cycle_step]
        moving = state in {"hauling", "returning"}
        loaded = state in {"loading", "hauling"}
        idle = state in {"loading", "dumping"}

        speed = self.rng.uniform(24, 42) if moving else self.rng.uniform(0, 1.5)
        anomaly = self.rng.random() < self.anomaly_rate
        speeding = anomaly and moving
        if speeding:
            speed = self.rng.uniform(51, 62)

        distance_delta = speed * elapsed_seconds / 3600
        fuel_rate_lph = 88 if moving else 14
        fuel_delta = fuel_rate_lph * elapsed_seconds / 3600
        self.state.odometer_km += distance_delta
        self.state.total_fuel_litres += fuel_delta
        self.state.fuel_level_pct = max(0, self.state.fuel_level_pct - fuel_delta / 12)
        self.state.engine_hours += elapsed_seconds / 3600
        self.state.latitude += self.rng.uniform(-0.000020, 0.000020) if moving else 0
        self.state.longitude += self.rng.uniform(-0.000020, 0.000020) if moving else 0

        payload = self.rng.uniform(216, 228) if loaded else 0.0
        engine_temp = self.rng.uniform(86, 96)
        fault_codes: list[str] = []
        if anomaly and not speeding:
            engine_temp = self.rng.uniform(106, 115)
            fault_codes.append("ENG_OVERHEAT")

        measurements: dict[str, Any] = {
            "location": {
                "lat": round(self.state.latitude, 6),
                "lon": round(self.state.longitude, 6),
                "heading": round(self.rng.uniform(0, 359.9), 1),
                "speed_kmh": round(speed, 1),
                "zone": "Pit-A" if loaded else "Dump-A",
            },
            "haul_cycle": {
                "cycle_id": f"cycle-{self.asset.asset_id.lower()}-{self.state.cycle_index:05d}",
                "cycle_state": state,
                "payload_tonnes": round(payload, 1),
                "target_payload_tonnes": 240.0,
            },
            "fuel": {
                "total_litres": round(self.state.total_fuel_litres, 2),
                "level_pct": round(self.state.fuel_level_pct, 1),
                "engine_on": True,
                "idle_flag": idle,
            },
            "operating": {
                "engine_hours": round(self.state.engine_hours, 2),
                "odometer_km": round(self.state.odometer_km, 2),
                "geofence_violation": False,
                "harsh_braking_flag": False,
                "speeding_flag": speeding,
            },
            "diagnostics": {
                "engine_temp_c": round(engine_temp, 1),
                "battery_voltage": round(self.rng.uniform(23.8, 25.2), 1),
                "fault_codes": fault_codes,
                "health_index": round(0.72 if fault_codes else self.state.health_index, 3),
            },
        }

        self.state.cycle_step = (self.state.cycle_step + 1) % len(self._cycle_states)
        if self.state.cycle_step == 0:
            self.state.cycle_index += 1
        return measurements


class EquipmentHealthSimulator(Simulator):
    def _measurements(self, elapsed_seconds: float) -> dict[str, Any]:
        anomaly = self.rng.random() < self.anomaly_rate
        self.state.engine_hours += elapsed_seconds / 3600
        self.state.health_index = max(0.3, self.state.health_index - self.rng.uniform(0.0001, 0.0003))

        temperature = self.rng.uniform(68, 78)
        vibration = self.rng.uniform(3.5, 4.6)
        pressure = self.rng.uniform(2900, 3150)
        operating_state = "running"
        faults: list[str] = []
        if anomaly:
            temperature = self.rng.uniform(96, 108)
            vibration = self.rng.uniform(7.5, 10.0)
            operating_state = "faulted"
            faults = ["BEARING_OVERHEAT", "VIBRATION_HIGH"]

        return {
            "equipment_health": {
                "operating_state": operating_state,
                "bearing_temp_c": round(temperature, 1),
                "vibration_m_s2": round(vibration, 2),
                "hydraulic_pressure_psi": round(pressure, 1),
                "health_index": round(0.58 if anomaly else self.state.health_index, 3),
            },
            "operating": {
                "engine_hours": round(self.state.engine_hours, 2),
            },
            "diagnostics": {
                "battery_voltage": round(self.rng.uniform(23.8, 25.2), 1),
                "fault_codes": faults,
            },
        }


class EnvironmentalSimulator(Simulator):
    def _measurements(self, elapsed_seconds: float) -> dict[str, Any]:
        del elapsed_seconds
        anomaly = self.rng.random() < self.anomaly_rate
        pm2_5 = self.rng.uniform(8, 24)
        pm10 = self.rng.uniform(18, 48)
        if anomaly:
            pm2_5 = self.rng.uniform(55, 90)
            pm10 = self.rng.uniform(110, 180)

        return {
            "air_quality": {
                "pm2_5_ug_m3": round(pm2_5, 1),
                "pm10_ug_m3": round(pm10, 1),
                "dust_mg_m3": round(self.rng.uniform(0.05, 0.8), 2),
                "ambient_temp_c": round(self.rng.uniform(18, 34), 1),
                "relative_humidity_pct": round(self.rng.uniform(25, 75), 1),
                "alert_flag": anomaly,
            }
        }


def create_simulator(
    asset: AssetConfig,
    schema_version: str,
    anomaly_rate: float,
    rng: random.Random,
) -> Simulator:
    simulator_types = {
        "fleet": FleetSimulator,
        "equipment_health": EquipmentHealthSimulator,
        "environmental": EnvironmentalSimulator,
    }
    try:
        simulator_type = simulator_types[asset.domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported asset domain: {asset.domain}") from exc
    return simulator_type(asset, schema_version, anomaly_rate, rng)
