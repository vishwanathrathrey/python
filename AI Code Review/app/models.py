from dataclasses import dataclass, field

@dataclass
class ChangedFile:
    filename: str
    status: str
    patch: str

@dataclass
class ReviewFinding:
    category: str
    severity: str
    description: str
    recommendation: str
    line: int
    filename: str
    confidence: str = "Medium"

@dataclass
class ReviewReport:
    findings: list
    file_summary: dict = field(default_factory=dict)
    count_summary: dict = field(default_factory=dict)