import streamlit as st
import pandas as pd

pd.set_option('display.max_columns', 100)

def set_markdown():
    st.markdown(f'''<style>.css-91z34k {{max-width: 65rem; padding:1rem}};</style>''', unsafe_allow_html=True)
    st.markdown(f'''<style>.css-1vq4p4l {{padding:1rem}};</style>''', unsafe_allow_html=True)

def select_table():
    st.sidebar.header('1. Select Table')
    table_name = st.sidebar.selectbox('test', ['cvivpc_vbm_targets_wi_20230125_enr'], label_visibility='collapsed')
    return table_name

@st.cache(suppress_st_warning=True)
def load_data(table_name):
    df = pd.read_pickle(f'{table_name}.pkl')
    df = df.applymap(lambda s:s.upper() if type(s) == str else s)
    df = df.fillna('NULL')
    return df

def set_description(df, table_name):
    st.markdown('<h1 style="color:#3d539c; font-size: 30px; font-weight:bold;">Counts and Crosstabs</h1>', unsafe_allow_html=True)
    help = st.checkbox('What am I looking at? Help me!')
    if help:
        st.write("haha no...")
    description_dict = {
     'cvivpc_vbm_targets_wi_20230125_enr' : 'WI April General Vote By Mail Planning Universe from CVI/VPC [2023-01-25]'
    }
    st.markdown(f'<span>Table Name:\t\t</span><span style="font-size: 20px; font-weight:bold;">{table_name}</span>', unsafe_allow_html=True)

    if table_name in description_dict.keys():
        descrip = description_dict[table_name]
    else:
        descrip = 'None'

    st.markdown(f'<span>Table Description:\t\t</span><span style="font-size: 20px; font-weight:bold;">{descrip}</span>', unsafe_allow_html=True)
    st.markdown(f'<span>Total Rows:\t\t</span><span style="font-size: 20px; font-weight:bold;">{"{:,}".format(len(df))}</span>', unsafe_allow_html=True)

def display_all_counts(df, columns, sort):
    for col in columns:
        if sort == 'index':
            st.write(df[col].value_counts().sort_index().map('{:,.0f}'.format))
        else:
            st.write(df[col].value_counts().map('{:,.0f}'.format))

def sidebar_setup(df):
    st.sidebar.header('2. Select Variables')

    columns_with_few_unique_values = df.nunique()[df.nunique() < 300].index.tolist()

    col1, col2, col3 = st.sidebar.columns([2,1,1], gap="small")

    with col1:
        st.write("Display Counts for \n **All Variables**")
    with col2:
        A = st.button('By Index')
        # display_all_counts(df, columns_with_few_unique_values, 'index')
    with col3:
        B = st.button('By Value')
        # display_all_counts(df, columns_with_few_unique_values, 'value')

    if A:
        display_all_counts(df, columns_with_few_unique_values, 'index')
    if B:
        display_all_counts(df, columns_with_few_unique_values, 'value')

    st.sidebar.write('_... or select specific variables ..._')
    var1, var2 = None, None
    var1 = st.sidebar.selectbox('**VARIABLE 1 (ROWS)**', [None] + columns_with_few_unique_values)
    var1_alias = st.sidebar.text_input('VARIABLE 1 ALIAS (Optional)', '')
    st.sidebar.write("")
    st.sidebar.write("")
    var2 = st.sidebar.selectbox('**VARIABLE 2 (COLUMNS)**', [None] + columns_with_few_unique_values)
    var2_alias = st.sidebar.text_input('VARIABLE 2 ALIAS (Optional)', '')

    st.sidebar.header('3. Normalize By')
    norm = st.sidebar.selectbox('test', ['Total', None, 'Rows','Columns','Both (Row + Column)', 'All (Row + Column + Total)'], label_visibility='collapsed')

    norm = False if norm == None else norm
    norm = 'Rows' if norm == 'index' else norm

    return var1, var2, var1_alias, var2_alias, norm

def sort_crosstabs(df):
    def sort_columns(df):
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

    def sort_rows(df):
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

    df = sort_columns(df)
    df = sort_rows(df)
    return df

def add_aliases(df, var1_alias, var2_alias):
    if var1_alias != '':
        df.index = var1_alias + '_' + df.index
    if var2_alias != '':
        df.columns = var2_alias + '_' + df.columns
    return df

def non_crosstabs(df, var1, var2, var1_alias, var2_alias):
    if [var1,var2] == [None, None]:
        return
    elif var1 == None:
        crosstab = pd.crosstab(index=df[var2], columns='count').style.format("{:,.0f}")
        st.dataframe(crosstab)
    elif var2 == None:
        crosstab = pd.crosstab(index='count', columns=df[var1]).style.format("{:,.0f}")
        st.dataframe(crosstab)
    else:
        return

def crosstabs(df, var1, var2, var1_alias, var2_alias, norm):
    def count_crosstab(df, var1, var2, var1_alias, var2_alias):
        ct = pd.crosstab(df[var1], df[var2])
        ct.loc['TOTAL'] = ct.sum()
        ct['TOTAL'] = ct.sum(axis=1)
        ct = ct.applymap(lambda x: "{:,.0f}".format(x))
        ct = sort_crosstabs(ct)
        ct = add_aliases(ct, var1_alias, var2_alias)
        if len(ct) > 10:
            st.dataframe(ct, height=40*len(ct)+1)
        else:
            st.dataframe(ct)


    def normed_crosstab(df, var1, var2, var1_alias, var2_alias, norm):
        ct_norm = pd.DataFrame(pd.crosstab(df[var1], df[var2], margins=True, margins_name ='TOTAL', normalize=norm))
        ct_norm = ct_norm.applymap(lambda x: "{:.0f}%".format(x*100))
        ct_norm = sort_crosstabs(ct_norm)
        ct_norm = add_aliases(ct_norm, var1_alias, var2_alias)
        if len(ct_norm) > 10:
            st.dataframe(ct_norm, height=40*len(ct_norm)+1)
        else:
            st.dataframe(ct_norm)


    st.write(f'**Total Counts:**')
    count_crosstab(df, var1, var2, var1_alias, var2_alias)

    if norm in ['Rows','Both (Row + Column)','All (Row + Column + Total)']:
        st.write(f'**Percent of Row ({var1}):**')
        normed_crosstab(df, var1, var2, var1_alias, var2_alias, 'index')

    if norm in ['Columns','Both (Row + Column)','All (Row + Column + Total)']:
        st.write(f'**Percent of Column ({var2}):**')
        normed_crosstab(df, var1, var2, var1_alias, var2_alias, 'columns')

    if norm in ['Total','All (Row + Column + Total)']:
        st.write(f'**Percent of Total:**')
        normed_crosstab(df, var1, var2, var1_alias, var2_alias, 'all')

def generate(df, var1, var2, var1_alias, var2_alias, norm):
    if var1 == None or var2 == None:
        non_crosstabs(df, var1, var2, var1_alias, var2_alias)
    else:
        crosstabs(df, var1, var2, var1_alias, var2_alias, norm)

def main():
    set_markdown()
    table_name = select_table()
    df = load_data(table_name)
    set_description(df, table_name)
    [var1, var2, var1_alias, var2_alias, norm] = sidebar_setup(df)
    st.sidebar.write("")
    st.sidebar.write("")
    if st.sidebar.button('Go! Generate Crosstabs'):
        generate(df, var1, var2, var1_alias, var2_alias, norm)

if __name__ == "__main__":
    main()
