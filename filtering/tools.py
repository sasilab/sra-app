"""
Filtering data by a given label.
"""


def filter_dataframe_by_label(data, label):
    """
    ## Filter by a given label

    Labels need to be available as a column in the DataFrame and values need to be stored as Booleans.

    Input Arguments:
    - data (pandas DataFrame): DataFrame with the data to filter
    - label (String): The label to filter

    Returns:
    - filtered pandas DataFrame

    ---
    """
    if label not in data.columns:
        raise ValueError(f"Missing required column: {label}")

    return data[data[label] == True]
