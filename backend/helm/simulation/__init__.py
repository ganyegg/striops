"""Decision Simulator — the flagship "What happens if..." engine.

Every simulation compares a scenario against the baseline across financial,
operational, citizen, environmental, political and risk dimensions, and returns
a recommendation with confidence and evidence.
"""
from helm.simulation.engine import list_scenarios, simulate

__all__ = ["simulate", "list_scenarios"]
