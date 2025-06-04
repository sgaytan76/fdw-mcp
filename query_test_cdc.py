import oracledb
import os
from dotenv import load_dotenv
from tabulate import tabulate

def fetch_test_cdc_rows():
    # Load environment variables
    load_dotenv()
    
    # Get database credentials from environment variables
    username = os.getenv('ORACLE_USER')
    password = os.getenv('ORACLE_PASSWORD')
    dsn = os.getenv('ORACLE_DSN')
    
    try:
        # Initialize oracle client
        oracledb.init_oracle_client()
        
        # Create a connection
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        cursor = connection.cursor()
        
        # Execute the query
        cursor.execute("SELECT * FROM TEST_CDC WHERE ROWNUM <= 10")
        
        # Fetch column names
        columns = [d[0] for d in cursor.description]
        
        # Fetch rows
        rows = cursor.fetchall()
        
        # Print results in a table format
        print(tabulate(rows, headers=columns, tablefmt='grid'))
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    fetch_test_cdc_rows() 