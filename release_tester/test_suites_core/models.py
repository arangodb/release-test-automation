from dataclasses import dataclass, field


@dataclass
class RtaTestResult:
    """test result"""
    success: bool = field()
    name: str = field(default="")
    message: str = field(default="")
    traceback: str = field(default="")
