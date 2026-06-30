from dataclasses import dataclass

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

@dataclass
class ReviewReport:
    findings: list