from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class PipelineInfo:
    pipeline_id: str
    display_name: str
    description: str
    created_at: datetime

    def to_dict(self):
        return asdict(self)