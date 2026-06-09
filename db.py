import sqlite3
import pandas as pd
import os

DB_PATH = "customer_intelligence.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(seed_file="sample_customers.csv"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop table if exists to ensure clean state
    cursor.execute("DROP TABLE IF EXISTS customers")
    
    # Create customers table
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE,
        name TEXT,
        age INTEGER,
        gender TEXT,
        location TEXT,
        income REAL,
        product_purchased TEXT,
        purchase_amount REAL,
        purchase_frequency INTEGER,
        emi_amount REAL,
        emi_tenure INTEGER,
        emi_status TEXT,
        subscription_type TEXT,
        subscription_expiry_date TEXT,
        last_purchase_date TEXT,
        engagement_score INTEGER,
        customer_satisfaction_score INTEGER,
        churned INTEGER
    )
    """)
    conn.commit()
    
    # Seed data
    if os.path.exists(seed_file):
        df = pd.read_csv(seed_file)
        
        # Insert into database
        for idx, row in df.iterrows():
            cursor.execute("""
            INSERT INTO customers (
                customer_id, name, age, gender, location, income, product_purchased,
                purchase_amount, purchase_frequency, emi_amount, emi_tenure, emi_status,
                subscription_type, subscription_expiry_date, last_purchase_date,
                engagement_score, customer_satisfaction_score, churned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["Customer ID"], row["Name"], int(row["Age"]), row["Gender"], row["Location"],
                float(row["Income"]), row["Product Purchased"], float(row["Purchase Amount"]),
                int(row["Purchase Frequency"]), float(row["EMI Amount"]), int(row["EMI Tenure"]),
                row["EMI Status"], row["Subscription Type"], row["Subscription Expiry Date"],
                row["Last Purchase Date"], int(row["Engagement Score"]), int(row["Customer Satisfaction Score"]),
                int(row["Churned"])
            ))
        conn.commit()
        print(f"Database seeded with {len(df)} records from {seed_file}.")
    else:
        print(f"Seed file {seed_file} not found. Empty database initialized.")
        
    conn.close()

def load_data_from_db():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def save_customer(cust_data):
    """
    Saves or updates a customer in the database.
    cust_data is a dictionary with database fields.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT id FROM customers WHERE customer_id = ?", (cust_data["customer_id"],))
    row = cursor.fetchone()
    
    if row:
        # Update
        cursor.execute("""
        UPDATE customers SET
            name = ?, age = ?, gender = ?, location = ?, income = ?, product_purchased = ?,
            purchase_amount = ?, purchase_frequency = ?, emi_amount = ?, emi_tenure = ?, emi_status = ?,
            subscription_type = ?, subscription_expiry_date = ?, last_purchase_date = ?,
            engagement_score = ?, customer_satisfaction_score = ?, churned = ?
        WHERE customer_id = ?
        """, (
            cust_data["name"], cust_data["age"], cust_data["gender"], cust_data["location"], cust_data["income"],
            cust_data["product_purchased"], cust_data["purchase_amount"], cust_data["purchase_frequency"],
            cust_data["emi_amount"], cust_data["emi_tenure"], cust_data["emi_status"],
            cust_data["subscription_type"], cust_data["subscription_expiry_date"], cust_data["last_purchase_date"],
            cust_data["engagement_score"], cust_data["customer_satisfaction_score"], cust_data["churned"],
            cust_data["customer_id"]
        ))
    else:
        # Insert
        cursor.execute("""
        INSERT INTO customers (
            customer_id, name, age, gender, location, income, product_purchased,
            purchase_amount, purchase_frequency, emi_amount, emi_tenure, emi_status,
            subscription_type, subscription_expiry_date, last_purchase_date,
            engagement_score, customer_satisfaction_score, churned
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cust_data["customer_id"], cust_data["name"], cust_data["age"], cust_data["gender"], cust_data["location"],
            cust_data["income"], cust_data["product_purchased"], cust_data["purchase_amount"], cust_data["purchase_frequency"],
            cust_data["emi_amount"], cust_data["emi_tenure"], cust_data["emi_status"],
            cust_data["subscription_type"], cust_data["subscription_expiry_date"], cust_data["last_purchase_date"],
            cust_data["engagement_score"], cust_data["customer_satisfaction_score"], cust_data["churned"]
        ))
    
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
