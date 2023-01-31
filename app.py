import streamlit as st
import pandas as pd
import os

pd.set_option('display.max_columns', 100)

def main():
    set_markdown()
    table_name = select_table()
    df = load_data(table_name)
    create_header(df, table_name)
    [var1, var2, var1_prefix, var2_prefix, norm] = sidebar_setup(df)
    st.sidebar.write("")
    st.sidebar.write("")
    generate(df, var1, var2, var1_prefix, var2_prefix, norm)

def set_markdown():
    """ Change default streamlit .css using markdown. Removes unnecessary header space. Make sure to include 'unsafe_allow_html=True'!! """
    st.markdown(f'''<style>.css-91z34k {{max-width: 65rem; padding:1rem}};</style>''', unsafe_allow_html=True)
    st.markdown(f'''<style>.css-1vq4p4l {{padding:1rem}};</style>''', unsafe_allow_html=True)

def select_table():
    """ Allow user to select table from available pickles in the pickles/ folder. Returns full pickle name (schema.table) as a string"""
    st.sidebar.header('1. Select Table')

    # Get list of pickles from folder, remove .pkl extension
    file_list = [f.replace('.pkl','') for f in os.listdir('pickles')]

    # Create selectbox for user to choose table name and return as string (without extension)
    return st.sidebar.selectbox('test', file_list, label_visibility='collapsed')

@st.cache(suppress_st_warning=True)
def load_data(table_name):
    """ Load pickle into dataframe and do basic transformations. Arguments: table_name (str). Returns df. """

    df = pd.read_pickle(f'pickles/{table_name}.pkl')

    # Convert string columns to UPPERCASE
    df = df.applymap(lambda s:s.upper() if type(s) == str else s)

    # Crude type conversion
    # If the word 'date' is in column name, convert to datetime and fill nulls with NaT (not a time)
    # Otherwise, fill nulls with string "NULL"
    for col in df.columns:
        if 'date' in col:
            df[col] = pd.to_datetime(df[col]).dt.date
            df[col] = df[col].fillna(pd.NaT)
        else:
            df[col] = df[col].fillna('NULL')
    return df

def create_header(df, table_name):
    """ Display header at the top of the page. Includes basic information like table name and the number of rows/columns. Also includes a "help" button. Arguments: dataframe and table name. Returns None."""

    # Title
    st.markdown('<h1 style="color:#3d539c; font-size: 30px; font-weight:bold;">Counts and Crosstabs</h1>', unsafe_allow_html=True)

    # Help box
    if st.checkbox('What am I looking at? Help me!'):
        st.write("➣ Check out the [ReadMe](https://github.com/SamLeBlanc/counts_crosstabs/blob/main/README.md)")

    # Table name
    st.markdown(f'<span style="padding-right: 5px;">Table Name:</span><span style="font-size: 20px; font-weight:bold;">{table_name}</span>', unsafe_allow_html=True)

    # Table shape
    st.markdown(f"""
        <span style="padding-right: 5px;">Table Shape:</span>
        <span style="font-size: 20px; font-weight:bold;">{"{:,}".format(df.shape[0])} rows</span>
        <span style="padding: 0px 5px;">and</span>
        <span style="font-size: 20px; font-weight:bold;">{"{:,}".format(df.shape[1])} columns</span>
    """, unsafe_allow_html=True)

def display_all_counts(df, columns, sort):
    """ Display the value counts of (almost) all variables in dataframe as a list of tables in main feed. User selection indicates whether to sort by valu or by index. Arguments: dataframe, column name, sorting method. Returns: None"""

    def sort_counts(df, col, sort):
        """ Sort the value counts according to user input"""
        # Sort normally (by count value) to begin with
        df_ = df[col].value_counts(dropna=False)
        # If user wants to sort by index, try
        # Sort weird types will not sort by index so use try/except
        if sort == 'index':
            try:
                df_ = df[col].value_counts(dropna=False).sort_index()
            except:
                pass
        return df_

    # Iterate through columns, display value counts for each column
    for col in columns:
        df_ = sort_counts(df, col, sort)
        try:
            df_ = df_.map('{:,.0f}'.format) # format with comma if applicable
        except:
            pass
        st.write(df_)

def sidebar_setup(df):
    """ Create user selection options in sidebar (other than table select) and collect user settings to use in crosstab generations. Arguments: dataframe. Returns the names, prefixes, and norm to use when generating crosstabs. """

    st.sidebar.header('2. Select Variables')

    col1, col2, col3 = st.sidebar.columns([1.3,1,1], gap="small")
    with col1: st.write("Show Counts for \n **All Variables**")
    with col2: A = st.button('Sort By Index')
    with col3: B = st.button('Sort By Value')

    # Limit to variables with less than 300 unique values. This will remove things like IDs from being in the variable selection
    columns_with_few_unique_values = df.nunique()[df.nunique() < 300].index.tolist()

    # User may choose to display counts for all variables using "Sort By .." button
    if A: display_all_counts(df, columns_with_few_unique_values, 'index')
    if B: display_all_counts(df, columns_with_few_unique_values, 'value')

    st.sidebar.write('_... **OR** choose specific variables below. you can select just one variable to see counts, or select two variables to see crosstabs ..._')

    # Initialize variables as None type
    # Assign variables and prefixes v=based on user selections
    var1, var2 = None, None
    var1 = st.sidebar.selectbox('**VARIABLE 1 (ROWS)**', [None] + columns_with_few_unique_values)
    var1_prefix = st.sidebar.text_input('VARIABLE 1 PREFIX (Optional)', '')
    st.sidebar.write("");st.sidebar.write("");

    var2 = st.sidebar.selectbox('**VARIABLE 2 (COLUMNS)**', [None] + columns_with_few_unique_values)
    var2_prefix = st.sidebar.text_input('VARIABLE 2 PREFIX (Optional)', '')

    # Allow user to normalize (create percentages) based on sum of rows, columns, or all values

    st.sidebar.header('3. Normalize By')
    norm = st.sidebar.selectbox('test', ['Total', None, 'Rows','Columns','Both (Row + Column)', 'All (Row + Column + Total)'], label_visibility='collapsed')

    return var1, var2, var1_prefix, var2_prefix, norm

def sort_crosstabs(df):
    """ Very ugly method :( but it sorts the columns and rows of the crosstab. Gernally, they will be sorted in alphabetical order, except with NULL appearing at the end with TOTAL. This sorting is done PRIOR to adding the prefix, so the prefix has no effect on sorting. Accepts and returns a crosstab dataframe. """
    def sort_crosstab_columns(df):
        try:
            lis = list(df.columns)
            for item in ['NULL','TOTAL']:
                try:
                    lis.remove(item)
                except:
                    pass
            lis = sorted(lis)
            for item in ['NULL','TOTAL']:
                if item in df.columns:
                    lis.append(item)
            df = df[lis]
            return df
        except:
            return df

    def sort_crosstab_rows(df):
        try:
            rows = list(df.index)
            df_ = df.copy(deep=True)
            for item in ['NULL','TOTAL']:
                try:
                    df_ = df_.drop(index=item)
                except:
                    pass
            df_ = df_.sort_index(ascending=True)
            for item in ['NULL','TOTAL']:
                if item in rows:
                    df_ = df_.append(df.loc[item])
            return df_
        except:
            pass

    df = sort_crosstab_columns(df)
    df = sort_crosstab_rows(df)
    return df

def add_prefixes(df, var1_prefix, var2_prefix):
    """ Apply the prefixes provided by the user. These help identify which column the value came from, which is espcially helpful for dealing with things like VCI and VProp, which have the same bucket names. Arguments: dataframe and both variable prefixes (default empty strings). Returns dataframe."""
    if var1_prefix != '':
        df.index = [var1_prefix + '_' + str(col) for col in df.index]
    if var2_prefix != '':
        df.columns = [var2_prefix + '_' + str(col) for col in df.columns]
    return df

def non_crosstabs(df, var1, var2):
    """ Display the 'crosstabs' for when a user provides only one variable. Hence, it is just a value counts table for one variable. Arguments: dataframe, both variable names (default empty string)"""

    if var1 == None and var2 != None:
        crosstab = pd.crosstab(index=df[var2], columns='count').style.format("{:,.0f}")
        st.dataframe(crosstab)
    elif var1 != None and var2 == None:
        crosstab = pd.crosstab(index='count', columns=df[var1]).style.format("{:,.0f}")
        st.dataframe(crosstab)

def crosstabs(df, var1, var2, var1_prefix, var2_prefix, norm):
    """ Create and display crosstabs for the chosen two variables. Modify crosstabs according to user selections about normalization and use of prefixes. May display between 1 and 4 crosstabs based on user selections. """

    def count_crosstab(df, var1, var2, var1_prefix, var2_prefix):
        """ Display un-normalized crosstab of variable 1 and variable 2. Include the totals for both rows and columns, format the crosstab with commas, sort the rows/columns mostly alphabetically, and add prefixes to the row/column names, if applicable."""

        ct = pd.crosstab(df[var1], df[var2])
        ct.loc['TOTAL'] = ct.sum()
        ct['TOTAL'] = ct.sum(axis=1)
        ct = ct.applymap(lambda x: "{:,.0f}".format(x))
        ct = sort_crosstabs(ct)
        ct = add_prefixes(ct, var1_prefix, var2_prefix)
        st.dataframe(ct)

    def normed_crosstab(df, var1, var2, var1_prefix, var2_prefix, norm):
        """ Exact same as 'count_crosstabs()' only this time we normalize (and format as percentages) """

        ct_norm = pd.DataFrame(pd.crosstab(df[var1], df[var2], margins=True, margins_name ='TOTAL', normalize=norm))
        ct_norm = ct_norm.applymap(lambda x: "{:.0f}%".format(x*100))
        ct_norm = sort_crosstabs(ct_norm)
        ct_norm = add_prefixes(ct_norm, var1_prefix, var2_prefix)
        st.dataframe(ct_norm)

    st.write(f'**Total Counts:**')
    # Always display counts crosstabs
    count_crosstab(df, var1, var2, var1_prefix, var2_prefix)

    # If requested, include normalized crosstabs with percentages
    if norm in ['Total','All (Row + Column + Total)']:
        st.write(f'**Percent of Total:**')
        normed_crosstab(df, var1, var2, var1_prefix, var2_prefix, 'all')
    if norm in ['Rows','Both (Row + Column)','All (Row + Column + Total)']:
        st.write(f'**Percent of Row ({var1}):**')
        normed_crosstab(df, var1, var2, var1_prefix, var2_prefix, 'index')
    if norm in ['Columns','Both (Row + Column)','All (Row + Column + Total)']:
        st.write(f'**Percent of Column ({var2}):**')
        normed_crosstab(df, var1, var2, var1_prefix, var2_prefix, 'columns')

def generate(df, var1, var2, var1_prefix, var2_prefix, norm):
    """ Generate the crosstabs based on user selections """
    if var1 == None or var2 == None:
        non_crosstabs(df, var1, var2)
    else:
        crosstabs(df, var1, var2, var1_prefix, var2_prefix, norm)

if __name__ == "__main__":
    main()
