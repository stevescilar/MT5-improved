from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SwingRef:
    type: str
    level: float
    index: int


@dataclass
class FVGRef:
    type: str
    top: float
    bottom: float
    index: int


@dataclass
class OrderBlockRef:
    type: str
    top: float
    bottom: float
    index: int


@dataclass
class DisplacementRef:
    type: str
    index: int
    body: float


@dataclass
class TradeSetup:
    direction: str
    sweep: Optional[dict] = field(default=None)
    choch: Optional[SwingRef] = field(default=None)
    displacement: Optional[DisplacementRef] = field(default=None)
    fvg: Optional[FVGRef] = field(default=None)
    order_block: Optional[OrderBlockRef] = field(default=None)
    entry: Optional[float] = field(default=None)
    stop: Optional[float] = field(default=None)
    target: Optional[float] = field(default=None)
    risk_reward: Optional[float] = field(default=None)
    valid: bool = False

    def has_full_model(self) -> bool:
        return all(
            [
                self.sweep is not None,
                self.choch is not None,
                self.displacement is not None,
                self.fvg is not None,
                self.order_block is not None,
            ]
        )

    def has_entry_trigger(self) -> bool:
        return all(
            [
                self.choch is not None,
                self.displacement is not None,
                self.entry is not None,
                self.stop is not None,
            ]
        )

    def has_refinement(self) -> bool:
        return self.entry is not None and self.stop is not None
