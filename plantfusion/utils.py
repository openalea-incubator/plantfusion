import os
import warnings


def save_df_to_csv(df, outputs_filepath, precision):
    """Save pandas dataframes to csv

    Parameters
    ----------
    df : pandas.DataFrame
        a pandas dataframe to be saved
    outputs_filepath : str
        the name of the CSV file to be saved
    precision : int
        number of decimals in CSV file
    """    

    try:
        df.to_csv(outputs_filepath, na_rep="NA", index=False, float_format="%.{}f".format(precision))
    except IOError as err:
        path, filename = os.path.split(outputs_filepath)
        filename = os.path.splitext(filename)[0]
        newfilename = "ACTUAL_{}.csv".format(filename)
        newpath = os.path.join(path, newfilename)
        df.to_csv(newpath, na_rep="NA", index=False, float_format="%.{}f".format(precision))
        warnings.warn("[{}] {}".format(err.errno, err.strerror))
        warnings.warn("File will be saved at {}".format(newpath))


def create_child_folder(parentfolderpath, childfolderpath):
    """Create a child folder from parent folder path

    Parameters
    ----------
    parentfolderpath : string
        parent folder path
    childfolderpath : string
        name of the child folder
    """    
    dirName = os.path.join(os.path.normpath(parentfolderpath), os.path.normpath(childfolderpath))
    try:
        # Create target Directory
        os.mkdir(dirName)
        print("Directory ", dirName, " Created ")
    except FileExistsError:
        print("Directory ", dirName, " already exists")
