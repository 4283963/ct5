import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHUNK_DIR: Path = DATA_DIR / "chunks"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    SAMPLE_DIR: Path = DATA_DIR / "sample"

    CHUNK_SIZE: int = 5 * 1024 * 1024

    CORS_ORIGINS: list = None

    FUEL_EFFICIENCY_THRESHOLD: float = 25.0
    SPEED_OPTIMAL_RANGE: tuple = (12, 18)
    WIND_IMPACT_THRESHOLD: float = 15.0

    IQR_THRESHOLD: float = 1.5
    ANOMALY_CONTAMINATION: float = 0.02
    VOYAGE_GAP_HOURS: int = 6
    WINDOW_SIZE: int = 20
    MIN_SPEED: float = 8
    MAX_SPEED: float = 40
    MIN_FUEL: float = 10
    MAX_FUEL: float = 100

    FUEL_TYPES: dict = None
    DEFAULT_FUEL_CONSUMPTION_RATE: float = 45.0
    CARBON_EMISSION_MAX_GAUGE: float = 100.0

    def __post_init__(self):
        self.CORS_ORIGINS = [
            "http://localhost:5173",
            "http://localhost:3000",
        ]
        self.FUEL_TYPES = {
            "HFO": {
                "name": "重油 (HFO)",
                "carbon_factor": 3.114,
                "density": 0.991,
                "sulfur_content": 0.035
            },
            "MGO": {
                "name": "船用柴油 (MGO)",
                "carbon_factor": 3.206,
                "density": 0.850,
                "sulfur_content": 0.005
            },
            "LNG": {
                "name": "液化天然气 (LNG)",
                "carbon_factor": 2.750,
                "density": 0.450,
                "sulfur_content": 0.0001
            },
            "VLSFO": {
                "name": "低硫燃油 (VLSFO)",
                "carbon_factor": 3.100,
                "density": 0.960,
                "sulfur_content": 0.005
            }
        }
        for directory in [self.DATA_DIR, self.UPLOAD_DIR, self.CHUNK_DIR,
                           self.PROCESSED_DIR, self.SAMPLE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
