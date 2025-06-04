"""
The SRA can be used in two ways.

1. as a pipeline directly in the code (see main.py)
2. with a user interface (see app.py)

This is the main file which allows the user to build a pipeline executing most of the SRA steps in order.

The recommended way is:
1. Load Data
2. Filter the Data
3. Calculate effective irradiation and temperature
4. Calculate the power matrix

The main.py pipeline is just an example and should not be seen as 'complete'. Use it to build your own
pipeline. The recommended way is to use the GUI. See app.py.
"""

import pandas as pd

from pipeline.pipe import DataPipeline
from pipeline.steps import ProcessingStep
from pipeline.functions import normalize_curve_data

from sra.temperature import cell_from_module_temperature
from sra.irradiance import effective_irradiance

from filtering.tools import filter_dataframe_by_label


def main():
    """
    ## Pipeline to execute some of the SRA steps.

    First init the pipeline:
    pipeline = DataPipeline()

    Then add steps like:
    pipeline.add_step(
        ProcessingStep(name="Normalize", function=normalize_curve_data)
    )

    Add input data, then run the pipeline:
    input_data = pd.read_pickle("data/Dataset4000Updated.pkl")
    result = pipeline.process(input_data)

    Each step will be executed in order and return an updated dataframe.
    """
    # success = create_new_project("Test Project")
    success = True
    if success:
        pipeline = DataPipeline()
        pipeline.add_step(
            ProcessingStep(name="Normalize", function=normalize_curve_data)
        )

        pipeline.add_step(
            ProcessingStep(
                name="Filter DataFrame",
                function=filter_dataframe_by_label,
                kwargs={"label": "Gut"},
            )
        )
        pipeline.add_step(
            ProcessingStep(
                name="Calculate Module Temperature",
                function=cell_from_module_temperature,
            )
        )
        pipeline.add_step(
            ProcessingStep(
                name="Effective Irradiance",
                function=effective_irradiance,
                kwargs={"isc_calibrated": 10.14, "isc_alpha": 0.06},
            )
        )

        input_data = pd.read_pickle("data/Dataset4000Updated.pkl")
        result = pipeline.process(input_data)
        print("\nFinal result:")
        print(result)
    else:
        print("Could not create a new project.")


if __name__ == "__main__":
    main()
