import oracledb
import os
import csv
from dotenv import load_dotenv

def export_test_cdc_to_csv(filename="test_cdc_export.csv"):
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
        
        # Get column names
        columns = [d[0] for d in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(columns)  # Write headers
            csvwriter.writerows(rows)    # Write data rows
            
        print(f"Data exported successfully to {filename}")
        print(f"Total rows exported: {len(rows)}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    export_test_cdc_to_csv() 