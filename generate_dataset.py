import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_sample_dataset(n_records=150, filename="sample_customers.csv"):
    np.random.seed(42)
    random.seed(42)
    
    first_names = ["John", "Jane", "Robert", "Mary", "Michael", "Patricia", "William", "Linda", "David", "Elizabeth", 
                   "Richard", "Barbara", "Joseph", "Susan", "Thomas", "Jessica", "Charles", "Sarah", "Christopher", "Karen",
                   "Daniel", "Nancy", "Matthew", "Lisa", "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra",
                   "Steven", "Ashley", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
                  "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"]
    
    locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    genders = ["Male", "Female", "Non-binary"]
    products = ["Electronics", "Fashion", "Home Appliances", "Books", "Fitness Gear", "Beauty Products", "Sports Equipment", "Office Supplies"]
    sub_types = ["None", "Basic", "Standard", "Premium"]
    emi_statuses = ["N/A", "Active", "Paid", "Defaulted"]
    
    records = []
    
    today = datetime.now()
    
    for i in range(1, n_records + 1):
        cust_id = f"CUST-{1000 + i}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = int(np.random.normal(40, 12))
        age = max(18, min(80, age))
        
        gender = random.choice(genders)
        location = random.choice(locations)
        
        # Income correlates slightly with age
        base_income = 30000 + (age - 18) * 1000
        income = int(np.random.normal(base_income, 15000))
        income = max(15000, min(200000, income))
        
        # Product purchased
        product_purchased = random.choice(products)
        
        # Purchase frequency correlates with income and age
        freq_base = 3 + (income / 30000)
        purchase_frequency = int(np.random.normal(freq_base, 3))
        purchase_frequency = max(1, min(50, purchase_frequency))
        
        # Purchase amount
        amt_base = 100 + (income / 1000)
        purchase_amount = float(np.random.normal(amt_base, 200))
        purchase_amount = round(max(20.0, purchase_amount), 2)
        
        # EMI details
        emi_status = random.choice(emi_statuses)
        if emi_status == "N/A":
            emi_amount = 0.0
            emi_tenure = 0
        else:
            emi_amount = round(purchase_amount * random.uniform(0.05, 0.15), 2)
            emi_tenure = random.choice([3, 6, 12, 18, 24])
            
        subscription_type = random.choice(sub_types)
        if subscription_type == "None":
            sub_expiry = "N/A"
        else:
            # subscription expiry: some in past (expired), some in future
            days_offset = random.randint(-180, 180)
            expiry_date = today + timedelta(days=days_offset)
            sub_expiry = expiry_date.strftime("%Y-%m-%d")
            
        # Last purchase date
        days_since_last = random.randint(1, 365)
        last_purchase = today - timedelta(days=days_since_last)
        last_purchase_date = last_purchase.strftime("%Y-%m-%d")
        
        # Engagement score
        engagement_score = int(np.random.normal(6, 2))
        engagement_score = max(1, min(10, engagement_score))
        
        # Customer satisfaction
        satisfaction_score = int(np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.15, 0.25, 0.35, 0.15]))
        
        # Adjust features to make churn predictable
        # Churn risk increases if last purchase is long ago, satisfaction is low, engagement is low, or EMI is defaulted
        churn_prob = 0.05
        if days_since_last > 180:
            churn_prob += 0.30
            engagement_score = max(1, engagement_score - 2)
        if satisfaction_score <= 2:
            churn_prob += 0.25
            engagement_score = max(1, engagement_score - 1)
        if emi_status == "Defaulted":
            churn_prob += 0.35
            engagement_score = max(1, engagement_score - 3)
        if subscription_type != "None" and days_offset < 0:
            # expired subscription
            churn_prob += 0.15
            
        churn_prob = min(0.95, max(0.02, churn_prob))
        churned = 1 if random.random() < churn_prob else 0
        
        records.append({
            "Customer ID": cust_id,
            "Name": name,
            "Age": age,
            "Gender": gender,
            "Location": location,
            "Income": income,
            "Product Purchased": product_purchased,
            "Purchase Amount": purchase_amount,
            "Purchase Frequency": purchase_frequency,
            "EMI Amount": emi_amount,
            "EMI Tenure": emi_tenure,
            "EMI Status": emi_status,
            "Subscription Type": subscription_type,
            "Subscription Expiry Date": sub_expiry,
            "Last Purchase Date": last_purchase_date,
            "Engagement Score": engagement_score,
            "Customer Satisfaction Score": satisfaction_score,
            "Churned": churned  # target column for classification models
        })
        
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    print(f"Generated {n_records} customer records in '{filename}'.")
    return df

if __name__ == "__main__":
    generate_sample_dataset()
