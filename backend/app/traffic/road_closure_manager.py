from datetime import datetime
import logging
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ActiveRoadClosure(BaseModel):
    closure_id: str
    u: int
    v: int
    key: int = 0
    reason: str
    severity: str = Field(default="impassable", description="'impassable', 'hazardous', 'flood'")
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
    metadata: Dict[str, str] = Field(default_factory=dict)


class RoadClosureManager:
    """
    Manages active emergency road closures and blocks.
    Maintains the closed edge set used by the MultiGraphAdapter to prune blocked edges.
    """

    def __init__(self):
        self._closures: Dict[str, ActiveRoadClosure] = {}
        # Fast lookup set of (u, v, key)
        self._closed_edges_set: Set[Tuple[int, int, int]] = set()

    def add_closure(
        self,
        closure_id: str,
        u: int,
        v: int,
        key: int = 0,
        reason: str = "Emergency incident obstruction",
        severity: str = "impassable",
        metadata: Optional[Dict[str, str]] = None
    ) -> ActiveRoadClosure:
        """Adds a road closure to the active set."""
        closure = ActiveRoadClosure(
            closure_id=closure_id,
            u=u,
            v=v,
            key=key,
            reason=reason,
            severity=severity,
            metadata=metadata or {}
        )
        self._closures[closure_id] = closure
        self._closed_edges_set.add((u, v, key))
        logger.warning(f"Road closure activated: {closure_id} on edge ({u} -> {v}, k={key}) - Reason: {reason}")
        return closure

    def remove_closure(self, closure_id: str) -> bool:
        """Lifts/removes an active road closure."""
        if closure_id in self._closures:
            closure = self._closures.pop(closure_id)
            self._closed_edges_set.discard((closure.u, closure.v, closure.key))
            logger.info(f"Road closure cleared: {closure_id} on edge ({closure.u} -> {closure.v}, k={closure.key})")
            return True
        return False

    def clear_all(self):
        """Clears all active closures."""
        self._closures.clear()
        self._closed_edges_set.clear()

    def get_closed_edges(self) -> Set[Tuple[int, int, int]]:
        """Returns the set of (u, v, key) tuples currently impassable."""
        return set(self._closed_edges_set)

    def list_closures(self) -> List[ActiveRoadClosure]:
        return list(self._closures.values())

    def is_closed(self, u: int, v: int, key: int = 0) -> bool:
        return (u, v, key) in self._closed_edges_set or (u, v, -1) in self._closed_edges_set

