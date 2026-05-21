from __future__ import annotations

from pydantic import BaseModel, Field


class BessInput(BaseModel):
    soc: float = Field(..., description="State of charge in percent or 0..1 fraction.")
    t_cell: float = Field(..., description="Cell temperature in Celsius.")
    t_amb: float = Field(..., description="Ambient temperature in Celsius.")
    u: float = Field(..., description="Requested C-rate.")
    hvac: bool = Field(False, description="Whether HVAC/cooling is active.")
    direction: str = Field("DISCHARGE", description="CHARGE or DISCHARGE.")
    horizon_minutes: int = Field(15, description="Projection horizon in minutes.")
    price: float | None = Field(None, description="Optional energy price in PLN/MWh.")
    avg_24h_price: float | None = Field(None, description="Optional 24h average price in PLN/MWh.")
    std_24h_price: float | None = Field(None, description="Optional 24h price standard deviation.")
    profile: str = Field("SAFETY_FIRST", description="SAFETY_FIRST, REVENUE_FIRST or GRID_FIRST.")
    reserve_required_kw: float = Field(0.0, description="Optional grid reserve requirement.")


class AnchorGridResult(BaseModel):
    product: str
    advisory_only: bool
    state: str
    execution_mode: str
    operation: str
    requested_u: str
    recommended_u_safe: str
    recommended_u_safe_value: float
    thermal_margin: str
    predicted_max_temp: float
    forecast_confidence: str
    forecast_confidence_score: float
    forecast_confidence_label: str
    estimated_degradation_stress: str
    tension: float
    reasons: dict
    economics: dict
    source_legacy_assets: list[str]
    soc_projection_15m: str
    soc_start: float
    soc_end: float
    forecast: dict
    warnings: list[str]
    decision: str
    disclaimer: str
