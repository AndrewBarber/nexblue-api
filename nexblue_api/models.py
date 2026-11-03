"""Stable data models independent of Home Assistant."""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TokenBundle:
    """Tokens returned by NexBlue; callers must persist only the refresh token."""

    access_token: str
    refresh_token: str | None
    expires_in: int
    account_id: str | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "TokenBundle":
        """Create a token bundle and expose the stable Cognito account subject."""
        access_token = str(payload["access_token"])
        return cls(
            access_token=access_token,
            refresh_token=payload.get("refresh_token"),
            expires_in=int(payload.get("expires_in", 0)),
            account_id=_jwt_subject(access_token),
        )


@dataclass(frozen=True, slots=True)
class Charger:
    """A charger visible to the authenticated end user."""

    serial_number: str
    role: str | int | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Charger":
        return cls(serial_number=str(payload["serial_number"]), role=payload.get("role"))


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """Read-only charger telemetry normalized to API units (kW, kWh, A, V)."""

    serial_number: str
    protocol_version: str | None
    charging_state: int
    power_kw: float
    energy_kwh: float
    lifetime_energy_kwh: float
    is_lock: bool | None
    network_status: int | None
    is_disable: bool | None
    cable_current_limit_a: int | None
    circuit_fuse_a: int | None
    current_limit_a: int | None
    cable_lock_mode: int | None
    access_level: int | None
    phase_charging: int | None
    brightness_percent: int | None
    uk_reg: bool | None
    current_a: tuple[float, ...]
    voltage_v: tuple[int, ...]

    @classmethod
    def from_api(cls, serial_number: str, payload: dict[str, Any]) -> "ChargerStatus":
        return cls(
            serial_number=serial_number,
            protocol_version=_optional_str(payload.get("protocol_version")),
            charging_state=int(payload["charging_state"]),
            power_kw=float(payload.get("power", 0)),
            energy_kwh=float(payload.get("energy", 0)),
            lifetime_energy_kwh=float(payload.get("lifetime_energy", 0)),
            is_lock=_optional_bool(payload.get("is_lock")),
            network_status=_optional_int(payload.get("network_status")),
            is_disable=_optional_bool(payload.get("is_disable")),
            cable_current_limit_a=_optional_int(payload.get("cable_current_limit")),
            circuit_fuse_a=_optional_int(payload.get("circuit_fuse")),
            current_limit_a=_optional_int(payload.get("current_limit")),
            cable_lock_mode=_optional_int(payload.get("cable_lock_mode")),
            access_level=_optional_int(payload.get("access_level")),
            phase_charging=_optional_int(payload.get("phase_charging")),
            brightness_percent=_optional_int(payload.get("brightness")),
            uk_reg=_optional_bool(payload.get("uk_reg")),
            current_a=tuple(float(value) for value in payload.get("current_list", [])),
            voltage_v=tuple(int(value) for value in payload.get("voltage_list", [])),
        )


@dataclass(frozen=True, slots=True)
class ChargerSession:
    """A completed charging session; energy in kWh, times in UTC."""

    start_time: datetime | None
    end_time: datetime | None
    energy_kwh: float
    start_reason: str | None
    stop_reason: str | None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "ChargerSession":
        return cls(
            start_time=_optional_timestamp(payload.get("start_timestamp")),
            end_time=_optional_timestamp(payload.get("end_timestamp")),
            energy_kwh=float(payload.get("consumption") or 0),
            start_reason=_optional_str(payload.get("start_reason")),
            stop_reason=_optional_str(payload.get("stop_reason")),
        )


def _optional_timestamp(value: Any) -> datetime | None:
    """Return a UTC time from a Unix timestamp when the API included one."""
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _optional_bool(value: Any) -> bool | None:
    """Return a bool when the API included one."""
    return value if isinstance(value, bool) else None


def _optional_int(value: Any) -> int | None:
    """Return an int when the API included an integer-like value."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    """Return a string when the API included a value."""
    return None if value is None else str(value)


def _jwt_subject(access_token: str) -> str | None:
    """Return the unverified Cognito JWT subject for a stable local account ID.

    The API gateway remains responsible for verifying token signatures. This
    value is used only as a local, stable identifier by API consumers.
    """
    parts = access_token.split(".")
    if len(parts) != 3:
        return None

    payload = parts[1]
    padded_payload = payload + "=" * (-len(payload) % 4)
    try:
        claims = json.loads(
            base64.b64decode(padded_payload, altchars=b"-_", validate=True)
        )
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        return None

    subject = claims.get("sub") if isinstance(claims, dict) else None
    return subject if isinstance(subject, str) and subject else None
