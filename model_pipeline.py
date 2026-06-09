import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def preprocess_data(df):
    """
    Cleans and preprocesses data for ML models.
    Computes helpful features and returns both raw and processed dataframes.
    """
    df_processed = df.copy()
    
    # Handle dates
    today = datetime.now()
    
    # Convert dates
    df_processed["Last Purchase Date"] = pd.to_datetime(df_processed["last_purchase_date"])
    df_processed["Days Since Last Purchase"] = (today - df_processed["Last Purchase Date"]).dt.days
    # Fill NaN or extreme values if any
    df_processed["Days Since Last Purchase"] = df_processed["Days Since Last Purchase"].fillna(180)
    
    # Subscription Expiry
    def parse_expiry(val):
        if pd.isna(val) or val == "N/A" or val == "":
            return 0
        try:
            exp_date = pd.to_datetime(val)
            return (exp_date - today).days
        except:
            return 0
            
    df_processed["Days to Subscription Expiry"] = df_processed["subscription_expiry_date"].apply(parse_expiry)
    df_processed["Is Subscription Expired"] = (df_processed["Days to Subscription Expiry"] < 0).astype(int)
    
    # Target columns
    df_processed["Churned"] = df_processed["churned"].fillna(0).astype(int)
    
    # Numerical features
    num_cols = ["age", "income", "purchase_amount", "purchase_frequency", 
                "emi_amount", "emi_tenure", "engagement_score", 
                "customer_satisfaction_score", "Days Since Last Purchase", 
                "Days to Subscription Expiry"]
    
    # Handle Categorical Columns
    label_encoders = {}
    cat_cols = ["gender", "location", "product_purchased", "emi_status", "subscription_type"]
    for col in cat_cols:
        le = LabelEncoder()
        df_processed[col + "_encoded"] = le.fit_transform(df_processed[col].astype(str))
        label_encoders[col] = le
        
    return df_processed, num_cols, label_encoders

def run_segmentation(df, num_clusters=5, algo='kmeans'):
    """
    Performs clustering (K-Means or Hierarchical) on customers
    and maps them to meaningful segments.
    """
    df_processed, num_cols, _ = preprocess_data(df)
    
    # Scale numeric features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_processed[num_cols])
    
    # Clustering
    if algo == 'hierarchical':
        model = AgglomerativeClustering(n_clusters=num_clusters)
        cluster_labels = model.fit_predict(scaled_features)
    else:
        model = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
        cluster_labels = model.fit_predict(scaled_features)
        
    df_processed["cluster"] = cluster_labels
    
    # PCA for plotting 2D scatter plots
    pca = PCA(n_components=2, random_state=42)
    pca_features = pca.fit_transform(scaled_features)
    df_processed["PC1"] = pca_features[:, 0]
    df_processed["PC2"] = pca_features[:, 1]
    
    # Analyze clusters to assign logical business segment names
    # Let's compute average features for each cluster
    cluster_stats = []
    for c in range(num_clusters):
        c_df = df_processed[df_processed["cluster"] == c]
        stats = {
            "cluster": c,
            "size": len(c_df),
            "mean_income": float(c_df["income"].mean()),
            "mean_purchase_amount": float(c_df["purchase_amount"].mean()),
            "mean_purchase_frequency": float(c_df["purchase_frequency"].mean()),
            "mean_engagement": float(c_df["engagement_score"].mean()),
            "mean_satisfaction": float(c_df["customer_satisfaction_score"].mean()),
            "mean_days_since_purchase": float(c_df["Days Since Last Purchase"].mean()),
            "mean_churn": float(c_df["Churned"].mean())
        }
        cluster_stats.append(stats)
        
    # Sort and label clusters based on properties:
    # High Value: high income, high purchase amount
    # Inactive: high days_since_purchase, low engagement
    # At-Risk: medium/high previous spending, low engagement, high churn
    # New Customers: low purchase frequency but low days_since_purchase
    # Regular Customers: moderate values across board
    # Occasional Buyers: low frequency, moderate amount, low engagement
    
    # We can rank the clusters using a scoring method, or rule-based matching:
    assigned_segments = {}
    available_labels = ["High Value Customers", "At-Risk Customers", "Inactive Customers", "New Customers", "Regular Customers", "Occasional Buyers"]
    
    # Let's label dynamically based on sorting
    # Sort cluster indices by a composite VIP score (purchase_amount * purchase_frequency)
    vip_scores = [s["mean_purchase_amount"] * s["mean_purchase_frequency"] for s in cluster_stats]
    sorted_by_vip = np.argsort(vip_scores)[::-1]
    
    # Sort by inactivity (days since purchase)
    inactivity_scores = [s["mean_days_since_purchase"] for s in cluster_stats]
    sorted_by_inactivity = np.argsort(inactivity_scores)[::-1]
    
    # Sort by churn / risk
    risk_scores = [s["mean_churn"] - 0.1 * s["mean_engagement"] for s in cluster_stats]
    sorted_by_risk = np.argsort(risk_scores)[::-1]
    
    # Assign labels based on priorities
    assigned_labels = [None] * num_clusters
    
    # 1. VIP (High Value) goes to the highest VIP score
    high_value_idx = sorted_by_vip[0]
    assigned_labels[high_value_idx] = "High Value Customers"
    
    # 2. Inactive goes to the highest inactivity (if not already assigned)
    for idx in sorted_by_inactivity:
        if assigned_labels[idx] is None:
            assigned_labels[idx] = "Inactive Customers"
            break
            
    # 3. At-Risk goes to highest risk (if not already assigned)
    for idx in sorted_by_risk:
        if assigned_labels[idx] is None:
            assigned_labels[idx] = "At-Risk Customers"
            break
            
    # 4. New Customers goes to lowest days since purchase + low frequency (if not already assigned)
    recency_scores = [s["mean_days_since_purchase"] for s in cluster_stats]
    sorted_by_recency = np.argsort(recency_scores)  # lowest is most recent
    for idx in sorted_by_recency:
        if assigned_labels[idx] is None:
            assigned_labels[idx] = "New Customers"
            break
            
    # 5. Regular Customers vs Occasional Buyers for any remainder
    for idx in range(num_clusters):
        if assigned_labels[idx] is None:
            # check frequency
            if cluster_stats[idx]["mean_purchase_frequency"] > df_processed["purchase_frequency"].median():
                assigned_labels[idx] = "Regular Customers"
            else:
                assigned_labels[idx] = "Occasional Buyers"
                
    # Map back to customers
    df_processed["segment"] = df_processed["cluster"].map(lambda c: assigned_labels[c])
    
    segment_stats = []
    for c in range(num_clusters):
        c_df = df_processed[df_processed["cluster"] == c]
        segment_stats.append({
            "cluster": c,
            "label": assigned_labels[c],
            "size": len(c_df),
            "percentage": round(100 * len(c_df) / len(df_processed), 2),
            "mean_income": round(c_df["income"].mean(), 2),
            "mean_purchase_amount": round(c_df["purchase_amount"].mean(), 2),
            "mean_purchase_frequency": round(c_df["purchase_frequency"].mean(), 2),
            "mean_engagement": round(c_df["engagement_score"].mean(), 2),
            "mean_satisfaction": round(c_df["customer_satisfaction_score"].mean(), 2),
            "mean_days_since_purchase": round(c_df["Days Since Last Purchase"].mean(), 2)
        })
        
    return df_processed, segment_stats

def train_classification_model(df, model_name="Random Forest"):
    """
    Trains a classification model to predict customer Churn.
    Returns:
       - dict of metrics (Accuracy, Precision, Recall, F1)
       - list of Churn Probabilities
       - dict of Feature Importances
    """
    df_processed, num_cols, label_encoders = preprocess_data(df)
    
    # Feature columns for classifier
    feature_cols = num_cols + [c + "_encoded" for c in ["gender", "location", "product_purchased", "emi_status", "subscription_type"]]
    
    # Remove target column if it slipped in
    feature_cols = [c for c in feature_cols if c not in ["Churned", "churned"]]
    
    X = df_processed[feature_cols]
    y = df_processed["Churned"]
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    if model_name == "Decision Tree":
        model = DecisionTreeClassifier(max_depth=5, random_state=42)
    elif model_name == "Logistic Regression":
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        model = LogisticRegression(random_state=42, max_iter=1000)
        X_train_for_model = X_train_scaled
        X_test_for_model = X_test_scaled
    elif model_name == "XGBoost":
        model = XGBClassifier(eval_metric='logloss', random_state=42)
    else: # Default: Random Forest
        model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        
    if model_name == "Logistic Regression":
        model.fit(X_train_for_model, y_train)
        y_pred = model.predict(X_test_for_model)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
    # Metrics
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0))
    }
    
    # Generate probabilities for the entire dataset
    if model_name == "Logistic Regression":
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        probs = model.predict_proba(X_scaled)[:, 1]
    else:
        probs = model.predict_proba(X)[:, 1]
        
    # Feature importances
    feature_importances = {}
    if model_name == "Logistic Regression":
        # use coefficients
        importances = np.abs(model.coef_[0])
        importances = importances / np.sum(importances)
    else:
        importances = model.feature_importances_
        
    for name, imp in zip(feature_cols, importances):
        # map clean name
        clean_name = name.replace("_encoded", "").replace("last_purchase_date_days", "Days Since Purchase").replace("age", "Age").replace("income", "Income").replace("purchase_amount", "Purchase Amount").replace("purchase_frequency", "Purchase Frequency").replace("emi_amount", "EMI Amount").replace("emi_tenure", "EMI Tenure").replace("engagement_score", "Engagement Score").replace("customer_satisfaction_score", "Customer Satisfaction Score")
        feature_importances[clean_name] = float(imp)
        
    # Sort feature importances
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))
    
    return metrics, probs, sorted_importances

def predict_purchase_behavior(df):
    """
    Predicts next purchased product category and future spending.
    Returns:
      - dict of customer ID -> next predicted product
      - dict of customer ID -> predicted next transaction amount
    """
    df_processed, num_cols, label_encoders = preprocess_data(df)
    
    # Features for predicting next product
    features_prod = ["age", "income", "purchase_frequency", "engagement_score", "customer_satisfaction_score", "gender_encoded", "location_encoded"]
    X_prod = df_processed[features_prod]
    y_prod = df_processed["product_purchased_encoded"]
    
    # Multiclass Random Forest for next product category
    clf_prod = RandomForestClassifier(n_estimators=50, random_state=42)
    clf_prod.fit(X_prod, y_prod)
    
    # Predict next product
    pred_encoded_prod = clf_prod.predict(X_prod)
    le = label_encoders["product_purchased"]
    pred_products = le.inverse_with_labels_or_simple_map = [le.classes_[p] for p in pred_encoded_prod]
    
    # Next spending prediction (Regression)
    # Features: age, income, purchase_frequency, purchase_amount, engagement_score, customer_satisfaction_score
    features_spend = ["age", "income", "purchase_frequency", "purchase_amount", "engagement_score"]
    X_spend = df_processed[features_spend]
    y_spend = df_processed["purchase_amount"] * (1 + np.random.normal(0.05, 0.02, len(df_processed))) # simulate future transaction size
    
    reg_spend = RandomForestRegressor(n_estimators=50, random_state=42)
    reg_spend.fit(X_spend, y_spend)
    pred_spending = reg_spend.predict(X_spend)
    
    customer_predictions = {}
    for i, row in df_processed.iterrows():
        customer_predictions[row["customer_id"]] = {
            "predicted_next_product": pred_products[i],
            "predicted_spending": round(float(pred_spending[i]), 2),
            "preferred_category": row["product_purchased"] # current preferred
        }
        
    return customer_predictions

def generate_personalized_recommendations(df, churn_probs, segments, purchase_preds):
    """
    Generates personalized offers, renewal dates, and loyalty rewards for each customer.
    """
    recs = {}
    
    for idx, row in df.iterrows():
        cid = row["customer_id"]
        prob = churn_probs[idx]
        segment = segments[idx]
        pred_prod = purchase_preds[cid]["predicted_next_product"]
        predicted_spend = purchase_preds[cid]["predicted_spending"]
        
        # Risk level
        if prob > 0.70:
            risk_level = "High"
        elif prob > 0.30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        # 1. Product Suggestion (upsell/cross-sell)
        product_suggestions = []
        if pred_prod == "Electronics":
            product_suggestions = ["Premium Wireless Headphones", "Smart Fitness Watch", "Ultra-Slim Power Bank"]
        elif pred_prod == "Fashion":
            product_suggestions = ["Designer Smart Casual Jacket", "Ergonomic Leather Footwear", "Premium Unisex Travel Bag"]
        elif pred_prod == "Home Appliances":
            product_suggestions = ["Smart Robot Vacuum Cleaner", "Instant Hot-Pot Multi-Cooker", "Air Purifier with HEPA Filter"]
        elif pred_prod == "Books":
            product_suggestions = ["Bestselling AI & Strategy Bundle", "Leadership & Executive Coaching Guide", "Self-Improvement Audiobooks Set"]
        elif pred_prod == "Fitness Gear":
            product_suggestions = ["Adjustable Smart Dumbbells", "Heavy Duty Anti-Slip Yoga Mat", "Waterproof Sports Tracker"]
        else:
            product_suggestions = ["Acoustic Noise-Cancelling Earbuds", "Classic Executive Fountain Pen", "Premium Everyday Leather Wallet"]
            
        # 2. Discount Offers
        discount_offer = "10% Off Sitewide"
        if risk_level == "High":
            discount_offer = f"Exclusive 30% Off Next Purchase: Use Code RENEW30"
        elif risk_level == "Medium":
            discount_offer = f"Exclusive 20% Off Next Purchase: Use Code SAVING20"
        elif segment == "High Value Customers":
            discount_offer = f"Exclusive 15% VIP Discount: Use Code VIP15"
            
        # 3. Renewal Reminders & EMI Renewal Plans
        renewal_reminder = "No upcoming renewals."
        emi_plan = "No active EMI plan recommended."
        
        if row["subscription_type"] != "None":
            # Check if expired or near expiry
            sub_exp = row["subscription_expiry_date"]
            if sub_exp != "N/A" and sub_exp != "":
                try:
                    exp_date = datetime.strptime(sub_exp, "%Y-%m-%d")
                    days_left = (exp_date - datetime.now()).days
                    if days_left < 0:
                        renewal_reminder = f"Your {row['subscription_type']} Subscription EXPIRED on {sub_exp}. Renew today for uninterrupted premium access!"
                    elif days_left < 30:
                        renewal_reminder = f"Your {row['subscription_type']} Subscription is expiring in {days_left} days ({sub_exp}). Renew now!"
                    else:
                        renewal_reminder = f"Subscription {row['subscription_type']} active until {sub_exp}."
                except:
                    pass
                    
        if row["emi_status"] == "Defaulted":
            emi_plan = "URGENT EMI Settlement Plan: Settle outstanding payments with 0% interest penalty waiver. Pay in 3 low installments."
        elif row["emi_status"] == "Active":
            emi_plan = f"Active EMI: ${row['emi_amount']}/mo for {row['emi_tenure']} mos. Next payment scheduled soon."
        elif row["emi_status"] == "Paid" or row["emi_status"] == "N/A":
            # Recommend a new low-interest EMI plan
            emi_plan = f"Pre-Approved EMI Plan: Upgrade to next-gen items with 0% interest EMI up to 12 months for purchases above $500!"
            
        # 4. Loyalty Rewards
        loyalty_points = int(row["purchase_amount"] * row["purchase_frequency"] / 10)
        loyalty_reward = f"{loyalty_points} Loyalty Points Available (Redeem for ${round(loyalty_points * 0.05, 2)} Cashback)"
        
        # 5. Retention Strategy
        if risk_level == "High" and segment == "High Value Customers":
            retention_strategy = "High-Priority VIP Intervention: Direct personal outreach by Customer Success Lead, offering an immediate 30% subscription discount or 1-on-1 account health-check."
        elif risk_level == "High":
            retention_strategy = "Active Winback Campaign: Targeted re-engagement email sequence with high-incentive 30% discount voucher and feature highlights."
        elif risk_level == "Medium":
            retention_strategy = "Feedback & Engagement Loop: Send personalized customer feedback survey and a 15% loyalty booster code."
        else:
            retention_strategy = "Nurture & Upsell: Keep engaged with regular newsletters, early product beta invites, and rewards program milestones."
            
        # CLV (Customer Lifetime Value) estimation
        clv = round(float(row["purchase_amount"] * row["purchase_frequency"] * 3.5), 2)
        
        recs[cid] = {
            "name": row["name"],
            "risk_level": risk_level,
            "churn_probability": round(float(prob), 4),
            "segment": segment,
            "product_suggestions": product_suggestions,
            "discount_offer": discount_offer,
            "renewal_reminder": renewal_reminder,
            "emi_plan": emi_plan,
            "loyalty_reward": loyalty_reward,
            "retention_strategy": retention_strategy,
            "clv": clv
        }
        
    return recs

def run_market_analysis(df):
    """
    Computes market trends, product performance, demand and revenue forecasting.
    """
    total_revenue = float(df["purchase_amount"].sum())
    avg_purchase = float(df["purchase_amount"].mean())
    
    # 1. Product performance (Sales distribution)
    product_counts = df["product_purchased"].value_counts()
    product_revenue = df.groupby("product_purchased")["purchase_amount"].sum()
    
    product_performance = []
    for prod in product_counts.index:
        product_performance.append({
            "product": prod,
            "units_sold": int(product_counts[prod]),
            "revenue": round(float(product_revenue[prod]), 2),
            "percentage_revenue": round(100 * float(product_revenue[prod]) / total_revenue, 2)
        })
        
    # 2. Seasonal purchase trends
    # Let's map Last Purchase Date to Seasons:
    # Mar-May: Spring, Jun-Aug: Summer, Sep-Nov: Autumn, Dec-Feb: Winter
    def get_season(date_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            if month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            elif month in [9, 10, 11]:
                return "Autumn"
            else:
                return "Winter"
        except:
            return "Summer"
            
    df_seasons = df.copy()
    df_seasons["season"] = df_seasons["last_purchase_date"].apply(get_season)
    season_counts = df_seasons["season"].value_counts()
    season_revenue = df_seasons.groupby("season")["purchase_amount"].sum()
    
    seasonal_trends = []
    for s in ["Spring", "Summer", "Autumn", "Winter"]:
        units = int(season_counts.get(s, 0))
        rev = float(season_revenue.get(s, 0.0))
        seasonal_trends.append({
            "season": s,
            "units_sold": units,
            "revenue": round(rev, 2)
        })
        
    # 3. Revenue Forecasting (Simple linear projection over the next 6 months)
    # Let's simulate historical month-by-month revenue for the past 6 months and forecast next 6 months
    # We will build a trend based on our current dataset size
    current_monthly_rev = total_revenue / 6.0 # assume the dataset is spread over 6 months
    
    months_ahead = ["July 2026", "August 2026", "September 2026", "October 2026", "November 2026", "December 2026"]
    forecasted_revenue = []
    
    # We can assume a minor growth rate, e.g. 3.5% month over month with small random variance
    np.random.seed(42)
    growth_rate = 0.035
    running_rev = current_monthly_rev
    
    for i, m in enumerate(months_ahead):
        running_rev = running_rev * (1 + growth_rate + np.random.normal(0, 0.01))
        forecasted_revenue.append({
            "month": m,
            "forecasted_revenue": round(float(running_rev), 2)
        })
        
    # 4. Product Demand Forecasting for next month
    demand_forecast = []
    for prod in product_counts.index:
        current_demand = int(product_counts[prod])
        # Project demand with a slight increase based on historical engagement scores
        avg_eng = float(df[df["product_purchased"] == prod]["engagement_score"].mean())
        projected_growth = 0.02 * (avg_eng - 5) # positive if engagement > 5, negative if < 5
        projected_demand = int(current_demand * (1 + projected_growth) / 6.0) # divided by 6 to estimate monthly demand
        projected_demand = max(5, projected_demand)
        
        demand_forecast.append({
            "product": prod,
            "current_monthly_average": round(current_demand / 6.0, 1),
            "projected_next_month_demand": projected_demand,
            "growth_trend": "Increasing" if projected_growth > 0 else "Decreasing/Stable"
        })
        
    return {
        "total_revenue": round(total_revenue, 2),
        "avg_purchase_amount": round(avg_purchase, 2),
        "product_performance": product_performance,
        "seasonal_trends": seasonal_trends,
        "revenue_forecast": forecasted_revenue,
        "demand_forecast": demand_forecast
    }
