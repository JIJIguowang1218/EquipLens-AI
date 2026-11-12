"""检索中引擎（P1）：契约、状态机、检查点、假适配器。"""

from .contracts import (Asset, Brief, PartRequirement, ResearchUnit, Target,
                        Verification, load_brief, validate_brief)
from .engine import RetrievalEngine
from .evidence import EvidenceStore
from .state import RunStore, new_state
from .web import NullLibraryAdapter, RuleVerifier, WebWorld

__all__ = [
    "Asset", "Brief", "PartRequirement", "ResearchUnit", "Target",
    "Verification", "load_brief", "validate_brief",
    "RetrievalEngine", "RunStore", "new_state", "EvidenceStore",
    "NullLibraryAdapter", "RuleVerifier", "WebWorld",
]
