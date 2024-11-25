import sqlite3

def clear_first_114_rows():
    """Remove the first 114 entries from the database"""
    try:
        # Connect to database
        conn = sqlite3.connect("dubai_tourism.db")
        cursor = conn.cursor()
        
        # Get current count
        cursor.execute("SELECT COUNT(*) FROM interactions")
        initial_count = cursor.fetchone()[0]
        
        # Delete first 114 rows using row_id
        cursor.execute("""
            DELETE FROM interactions 
            WHERE rowid IN (
                SELECT rowid 
                FROM interactions 
                ORDER BY rowid ASC 
                LIMIT 114
            )
        """)
        
        # Commit the changes
        conn.commit()
        
        # Get new count
        cursor.execute("SELECT COUNT(*) FROM interactions")
        final_count = cursor.fetchone()[0]
        
        print(f"Initial number of entries: {initial_count}")
        print(f"Removed {initial_count - final_count} entries")
        print(f"Current number of entries: {final_count}")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    response = input("Are you sure you want to delete the first 114 rows? (yes/no): ")
    if response.lower() == 'yes':
        clear_first_114_rows()
    else:
        print("Operation cancelled") 