import sys
import pandas as pd
import numpy as np

import boto3
import redshift_connector

import os
from dotenv import load_dotenv

import warnings
warnings.filterwarnings('ignore')

def main():
    res = parse_arguemnts()
    print(res)
    if res:
        df = get_table_from_redshift(res)
        create_pickle(res, df)

def parse_arguemnts():
    """ Parse the schema name and table name from the command line arguments. Returns a dictionary of form {'schema' : schema , 'table' : table} """
    args = sys.argv[1:] # drop script name from default args

    # ensure argument has proper format (e.g. schema.table)
    if len(args) != 1 or len(args[0].split('.')) != 2:
        print("Please provide exactly one command line argument of form 'schema.table'")
        return False
    else:
        schema = args[0].split('.')[0]
        table = args[0].split('.')[1]
        return {'schema' : schema , 'table' : table}

def establish_redshift_connection():
    """ Establish redshift connection using server info and environment variables, defined in .env file (see README.md) """
    try:
        print('\nAttempting Redshift connection...')
        load_dotenv() # load environemnt variables from .env
        conn = redshift_connector.connect(
             host='172.31.28.159',
             port=5439,
             database='analytics',
             user=os.environ['REDSHIFT_USERNAME'],     # defined in .env file
             password=os.environ['REDSHIFT_PASSWORD']  # defined in .env file
          )
        conn.rollback()
        conn.autocommit = True
        print('Success!\n')
        return conn.cursor()
    except Exception as e:
        print('Redshift connection failed (are you on VPN?)\n')
        print(e)

def get_table_from_redshift(res):
    """ Query Redshift for the table and column names. Return as a dataframe."""
    cursor = establish_redshift_connection()
    query = f"""select * from {res['schema']}.{res['table']}"""

    print(f"Querying Redshift with: {query} ")
    cursor.execute(query); # run query

    df = pd.DataFrame(cursor.fetchall(), dtype=str) # retrieve result as dataframe
    print(df.iloc[:5,:5]) # display head

    # query information schema for column names
    # (since these don't come with table by default)
    print(f"\nQuerying Redshift for column names...")
    cursor.execute(f"""
        select column_name
        from information_schema.columns
        where table_schema = '{res['schema']}' and table_name = '{res['table']}'
        order by ordinal_position;
    """);

    col_df = list(cursor.fetchall()) # retrieve column names as dataframe
    df.columns = [item for sublist in col_df for item in sublist] # set column names

    return df

def create_pickle(res, df):
    """ Save dataframe as pickle in pickles/ folder """
    save_location = f"pickles/{res['schema']}.{res['table']}.pkl"
    print(f"\nSaving to: {save_location}")
    df.to_pickle(save_location)
    print('\nDone!')

if __name__ == "__main__":
    main()
