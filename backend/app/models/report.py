from __future__ import annotations

from pydantic import BaseModel, Field


class FinalDiscoveryReport(BaseModel):
    title: str
    subtitle: str
    discovery_headline: str
    discovery_summary: str
    planet_overview: str
    chemistry_overview: str
    molecular_probe_overview: str
    spectrum_overview: str
    key_highlights: list[str] = Field(default_factory=list)
    caution_notes: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    novelty_tagline: str
