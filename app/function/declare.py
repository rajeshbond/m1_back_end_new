import pandas as pd

# Remove the duplicate from the operations 
def remove_duplicates(operation_list):
    """Normalize and remove duplicates from list of operations"""
    df_operation = pd.DataFrame(operation_list, columns=['operations'])
    df_operation['operations'] = df_operation['operations'].str.strip().str.lower()
    return df_operation.drop_duplicates(subset='operations', keep='first')
 
