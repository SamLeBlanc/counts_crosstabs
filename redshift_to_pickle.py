import sys
import pandas as pd
import numpy as np

import boto3
import redshift_connector

import os
from dotenv import load_dotenv

import warnings
warnings.filterwarnings('ignore')

def parse_arguemnts():
    args = sys.argv[1:]
    if len(args) > 1:
        print("Only accepts one command line argument of form 'schema.table'")
        return False
    elif len(args) < 1:
        print("Please provide one command line argument of form 'schema.table'")
        return False
    elif '.' not in args[0]:
        print("Please provide one command line argument of form 'schema.table'")
        return False
    else:
        schema = args[0].split('.')[0]
        table = args[0].split('.')[1]
        return [schema, table]

def establish_redshift_connection():
    """ Establish redshift connection using server info and environment variables """
    try:
        print('\nAttempting Redshift connection...')
        load_dotenv()
        conn = redshift_connector.connect(
             host='172.31.28.159',
             port=5439,
             database='analytics',
             user=os.environ['REDSHIFT_USERNAME'],     # defined in .env file
             password=os.environ['REDSHIFT_PASSWORD']  # defined in .env file
          )
        conn.rollback()
        conn.autocommit = True
        print('Successful Redshift connection!\n')
        cursor = conn.cursor()
        return cursor
    except Exception as e:
        print('Redshift connection failed (are you on VPN?)\n')
        print(e)

def create_pickle(res):
    cursor = establish_redshift_connection()

    schema = res[0]
    table = res[1]

    query = f"""select * from {schema}.{table}"""

    print(f"Querying Redshift with: {query} ")
    cursor.execute(query);
    df = pd.DataFrame(cursor.fetchall())
    print(df.iloc[:5,:5])

    print(f"\nQuerying Redshift for column names...")
    cursor.execute(f"""
        select column_name
        from information_schema.columns
        where
          table_schema = '{schema}'
          and table_name = '{table}'
        order by ordinal_position;
    """);

    col_df = list(cursor.fetchall())
    col_names = [item for sublist in col_df for item in sublist]

    df.columns = col_names

    save_location = f'pickles/{schema}.{table}.pkl'
    print(f"\nSaving to: {save_location}")
    df.to_pickle(save_location)
    print('\nDone!')

res = parse_arguemnts()
if res:
    create_pickle(res)
