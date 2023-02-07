# Redshift Counts and Crosstabs via Streamlit

A python-based, local Streamlit app which provides an easy way to view the counts and crosstabs of a table in the America Votes Redshift.

This app uses the python module [redshift-connector](https://pypi.org/project/redshift-connector/) to query a table in the AV Redshift. After the initial query, the full table is saved as a 'pickled' dataframe in the `pickles/` folder, which is then used to generate counts and crosstabs in the Streamlit app. 

This program is to be run locally only. To get new tables, the app requires your Redshift credentials to be saved as environmental variables in a `.env` file. This credentials file is stored locally and should never be uplaoded to GitHub. Note, the `.env` file is included in the `.gitignore` in case you push to this repo by mistake (but please don't).

## Getting Started

The estimated intital set-up time for this project is five minutes, after that, adding new tables is as fast as the `select * from table` command.

### 0. Install Python

To run this app, you must have Python (version > 3.7) installed on your system. You can install that [here](https://www.python.org/downloads/). 

Note, Python comes pre-installed on Mac OS X.

### 1. Clone the repository and move into the folder

In your terminal, run the following commands:

- `git clone https://github.com/AmericaVotes/Redshift-Counts-and-Crosstabs-via-Streamlit.git`

- `cd Redshift-Counts-and-Crosstabs-via-Streamlit`

### 2. In the root folder, create a `.env` file with your Redshift credentials

In order to access Redshift, you will need to create a file with environmental variables containing your Redshift username and password. The file must be stored in the main repository folder.

Format the file exactly as shown below, with identical variable names. The file should be named `.env`! Not `credentials.env` or `helloworld.env`, just `.env`

```
REDSHIFT_USERNAME=#########
REDSHIFT_PASSWORD=###############
```

### 3. Query Redshift for table and save results as a 'pickled' dataframe

In the terminal (and in the repo folder!), run the following command. Substitute the `{schema.table}` variable for the table that you want counts and crosstabs of.

- ```python redshift_to_pickle.py {schema.table}```

This function uses the credentials defined in the `.env` file to query Redshift and saves the table as a pickled dataframe in the `pickles/` folder. 

### 4. Open the Streamlit app from the command line to view counts and crosstabs!

Once the previous table has finished, run the following command to open Streamlit and view the counts and crosstabs.

- ```streamlit run app.py```

The app should open automatically and look something like this...
![image](https://user-images.githubusercontent.com/83605234/215891293-1156b3c1-8c96-4b13-a948-c35e181fa8c7.png)

## Viewing Counts and Crosstabs

1. Use the 'Select Table' selection box to choose the table of interest. Later on, if you want to add another table, re-run Step 3 from Getting Started section with a new `{schema.table}` variable.

2. After selecting the table, you can choose to see counts of all variables (by selecting the `Sort by ...`) or a single variable (by selecting the variable from the dropdowns under `Variable 1 (or 2)`. To view crosstabs, use the dropdowns to choose fields for both `Variable 1` and `Variable 2`.

3. By default, the app will normalize crosstabs (as percentages) over the total number of all records. Under the `Normalize By` drop down, the user can also select to normalize by row or by column.

### Prefixes

In the dataframe structure (which is a default of Streamlit), it is often hard to tell which variable the rows and columns are referring to. As an example, the buckets for VCI and VProp look identical, which makes deciphering the crosstabs more difficult. To improve clarity, users can apply a prefix to the rows/columns defined by that variable, making crosstabs more readable.

## Questions/Errors

If you encounter any unexpected errors or have any questions about this repository, please contact Sam at [sleblanc@americavotes.org]()
