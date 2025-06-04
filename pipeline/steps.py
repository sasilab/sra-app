from pydantic import BaseModel
from typing import Callable, Dict, Any


class ProcessingStep(BaseModel):
    """The structure of a pipeline step."""

    name: str
    function: Callable
    kwargs: Dict[str, Any] = None
