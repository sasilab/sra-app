"""
Overall structure of the DataPipeline
"""

import pandas as pd
from functools import reduce
from typing import List, Any
from .steps import ProcessingStep


class DataPipeline:
    """
    ## DataPipeline -> Used to process the SRA step by step

    Import this, then add steps and finally process. **See main.py**.
    """

    def __init__(self):
        self.steps: List[ProcessingStep] = []
        self.input_data: Any = None
        self.output_data: Any = None

    def add_step(self, step: ProcessingStep) -> None:
        """Adding a processing step."""
        self.steps.append(step)

    def process(self, input_data: pd.DataFrame) -> Any:
        """Process the pipe."""
        self.input_data = input_data

        def apply_step(data, step):
            print(f"Executing step: {step.name}")
            if step.kwargs is not None:
                return step.function(data, **step.kwargs)
            else:
                return step.function(data)

        self.output_data = reduce(apply_step, self.steps, input_data)
        return self.output_data
