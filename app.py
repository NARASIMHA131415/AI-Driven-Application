from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import numpy as np
import os
import json
import db
import model_pipeline
import reports

app = Flask(__name__)
app.secret_key = "customer_intelligence_secret_key"

# Ensure the database exists and is initialized
if not os.path.exists(db.DB_PATH):
    print("Database not found. Initializing...")
    if not os.path.exists("sample_customers.csv"):
        import generate_dataset
        generate_dataset.generate_sample_dataset()
    db.init_db()

@app.route("/")
def index():
    """
    Renders the main platform dashboard containing all panels and metrics.
    """
    # Load raw data from database
    df = db.load_data_from_db()
    
    if len(df) == 0:
        return render_template("index.html", empty_state=True)
        
    # Standard initial configuration for models
    num_clusters = 5
    clustering_algo = "kmeans"
    classifier_name = "Random Forest"
    
    # Run pipeline on default configurations
    df_seg, segment_stats = model_pipeline.run_segmentation(df, num_clusters=num_clusters, algo=clustering_algo)
    metrics, probs, importances = model_pipeline.train_classification_model(df, model_name=classifier_name)
    purchase_preds = model_pipeline.predict_purchase_behavior(df)
    recs = model_pipeline.generate_personalized_recommendations(df, probs, df_seg["segment"].values, purchase_preds)
    market_analysis = model_pipeline.run_market_analysis(df)
    
    # Format and join lists for frontend tables
    customers_list = []
    for idx, row in df.iterrows():
        cid = row["customer_id"]
        prob = probs[idx]
        segment = df_seg.iloc[idx]["segment"]
        rec_data = recs[cid]
        
        customers_list.append({
            "customer_id": cid,
            "name": row["name"],
            "age": int(row["age"]),
            "gender": row["gender"],
            "location": row["location"],
            "income": float(row["income"]),
            "product_purchased": row["product_purchased"],
            "purchase_amount": float(row["purchase_amount"]),
            "purchase_frequency": int(row["purchase_frequency"]),
            "emi_amount": float(row["emi_amount"]),
            "emi_tenure": int(row["emi_tenure"]),
            "emi_status": row["emi_status"],
            "subscription_type": row["subscription_type"],
            "subscription_expiry_date": row["subscription_expiry_date"],
            "last_purchase_date": row["last_purchase_date"],
            "engagement_score": int(row["engagement_score"]),
            "customer_satisfaction_score": int(row["customer_satisfaction_score"]),
            "segment": segment,
            "PC1": float(df_seg.iloc[idx]["PC1"]),
            "PC2": float(df_seg.iloc[idx]["PC2"]),
            "churn_probability": round(float(prob), 4),
            "risk_level": rec_data["risk_level"],
            "predicted_next_product": purchase_preds[cid]["predicted_next_product"],
            "predicted_spending": purchase_preds[cid]["predicted_spending"],
            "clv": rec_data["clv"],
            "discount_offer": rec_data["discount_offer"],
            "loyalty_reward": rec_data["loyalty_reward"],
            "retention_strategy": rec_data["retention_strategy"],
            "emi_plan": rec_data["emi_plan"],
            "renewal_reminder": rec_data["renewal_reminder"]
        })
        
    # Compute system stats
    total_revenue = market_analysis["total_revenue"]
    avg_order = market_analysis["avg_purchase_amount"]
    active_customers = len(df)
    high_risk_count = sum(1 for c in customers_list if c["risk_level"] == "High")
    avg_engagement = df["engagement_score"].mean()
    active_subs = sum(1 for idx, row in df.iterrows() if row["subscription_type"] != "None")
    
    # Send all variables to the template
    return render_template(
        "index.html",
        empty_state=False,
        customers=customers_list,
        segment_stats=segment_stats,
        metrics=metrics,
        importances=importances,
        market_analysis=market_analysis,
        selected_classifier=classifier_name,
        selected_clustering_algo=clustering_algo,
        selected_num_clusters=num_clusters,
        total_revenue=total_revenue,
        avg_order=avg_order,
        active_customers=active_customers,
        high_risk_count=high_risk_count,
        avg_engagement=round(avg_engagement, 2),
        active_subs=active_subs
    )

@app.route("/api/get_analytics", methods=["POST"])
def get_analytics():
    """
    Endpoint for asynchronous dashboard updates when model parameters are adjusted.
    """
    req_data = request.get_json() or {}
    classifier_name = req_data.get("classifier", "Random Forest")
    clustering_algo = req_data.get("clustering_algo", "kmeans")
    num_clusters = int(req_data.get("num_clusters", 5))
    
    df = db.load_data_from_db()
    
    if len(df) == 0:
        return jsonify({"error": "No customers found. Please seed or upload data."}), 400
        
    # Re-run pipeline with custom configurations
    df_seg, segment_stats = model_pipeline.run_segmentation(df, num_clusters=num_clusters, algo=clustering_algo)
    metrics, probs, importances = model_pipeline.train_classification_model(df, model_name=classifier_name)
    purchase_preds = model_pipeline.predict_purchase_behavior(df)
    recs = model_pipeline.generate_personalized_recommendations(df, probs, df_seg["segment"].values, purchase_preds)
    market_analysis = model_pipeline.run_market_analysis(df)
    
    # Format customer list
    customers_list = []
    for idx, row in df.iterrows():
        cid = row["customer_id"]
        prob = probs[idx]
        segment = df_seg.iloc[idx]["segment"]
        rec_data = recs[cid]
        
        customers_list.append({
            "customer_id": cid,
            "name": row["name"],
            "age": int(row["age"]),
            "gender": row["gender"],
            "location": row["location"],
            "income": float(row["income"]),
            "product_purchased": row["product_purchased"],
            "purchase_amount": float(row["purchase_amount"]),
            "purchase_frequency": int(row["purchase_frequency"]),
            "emi_amount": float(row["emi_amount"]),
            "emi_tenure": int(row["emi_tenure"]),
            "emi_status": row["emi_status"],
            "subscription_type": row["subscription_type"],
            "subscription_expiry_date": row["subscription_expiry_date"],
            "last_purchase_date": row["last_purchase_date"],
            "engagement_score": int(row["engagement_score"]),
            "customer_satisfaction_score": int(row["customer_satisfaction_score"]),
            "segment": segment,
            "PC1": float(df_seg.iloc[idx]["PC1"]),
            "PC2": float(df_seg.iloc[idx]["PC2"]),
            "churn_probability": round(float(prob), 4),
            "risk_level": rec_data["risk_level"],
            "predicted_next_product": purchase_preds[cid]["predicted_next_product"],
            "predicted_spending": purchase_preds[cid]["predicted_spending"],
            "clv": rec_data["clv"],
            "discount_offer": rec_data["discount_offer"],
            "loyalty_reward": rec_data["loyalty_reward"],
            "retention_strategy": rec_data["retention_strategy"],
            "emi_plan": rec_data["emi_plan"],
            "renewal_reminder": rec_data["renewal_reminder"]
        })
        
    high_risk_count = sum(1 for c in customers_list if c["risk_level"] == "High")
    
    response = {
        "customers": customers_list,
        "segment_stats": segment_stats,
        "metrics": metrics,
        "importances": importances,
        "market_analysis": market_analysis,
        "high_risk_count": high_risk_count
    }
    
    return jsonify(response)

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    """
    Handles uploaded CSV customer files, parses columns, maps them to schema, and stores to DB.
    """
    if "dataset" not in request.files:
        return redirect(url_for("index"))
        
    file = request.files["dataset"]
    if file.filename == "":
        return redirect(url_for("index"))
        
    if file and file.filename.endswith(".csv"):
        try:
            df_upload = pd.read_csv(file)
            
            # Map columns cleanly
            column_mapping = {}
            for col in df_upload.columns:
                clean_name = col.strip().lower().replace(" ", "_").replace("/", "_")
                # Handle special matches
                if "customer_id" in clean_name or "cust_id" in clean_name or "id" == clean_name:
                    column_mapping[col] = "customer_id"
                elif "name" in clean_name:
                    column_mapping[col] = "name"
                elif "age" in clean_name:
                    column_mapping[col] = "age"
                elif "gender" in clean_name:
                    column_mapping[col] = "gender"
                elif "location" in clean_name or "city" in clean_name or "address" in clean_name:
                    column_mapping[col] = "location"
                elif "income" in clean_name or "salary" in clean_name:
                    column_mapping[col] = "income"
                elif "product" in clean_name:
                    column_mapping[col] = "product_purchased"
                elif "amount" in clean_name or "spend" in clean_name:
                    if "emi" in clean_name:
                        column_mapping[col] = "emi_amount"
                    else:
                        column_mapping[col] = "purchase_amount"
                elif "frequency" in clean_name or "orders" in clean_name:
                    column_mapping[col] = "purchase_frequency"
                elif "emi_tenure" in clean_name or "tenure" in clean_name:
                    column_mapping[col] = "emi_tenure"
                elif "emi_status" in clean_name:
                    column_mapping[col] = "emi_status"
                elif "subscription_type" in clean_name or "subscription" in clean_name:
                    column_mapping[col] = "subscription_type"
                elif "expiry" in clean_name:
                    column_mapping[col] = "subscription_expiry_date"
                elif "last_purchase" in clean_name or "date" in clean_name:
                    column_mapping[col] = "last_purchase_date"
                elif "engagement" in clean_name:
                    column_mapping[col] = "engagement_score"
                elif "satisfaction" in clean_name or "csat" in clean_name:
                    column_mapping[col] = "customer_satisfaction_score"
                elif "churn" in clean_name:
                    column_mapping[col] = "churned"
                    
            # Rename matched columns
            df_upload = df_upload.rename(columns=column_mapping)
            
            # Check for core missing columns and fill with defaults
            required_cols = {
                "customer_id": lambda: f"CUST-{np.random.randint(2000, 9999)}",
                "name": lambda: "Unknown Client",
                "age": lambda: 35,
                "gender": lambda: "Male",
                "location": lambda: "Urban",
                "income": lambda: 50000.0,
                "product_purchased": lambda: "Electronics",
                "purchase_amount": lambda: 150.0,
                "purchase_frequency": lambda: 5,
                "emi_amount": lambda: 0.0,
                "emi_tenure": lambda: 0,
                "emi_status": lambda: "N/A",
                "subscription_type": lambda: "None",
                "subscription_expiry_date": lambda: "N/A",
                "last_purchase_date": lambda: pd.Timestamp.now().strftime("%Y-%m-%d"),
                "engagement_score": lambda: 5,
                "customer_satisfaction_score": lambda: 4,
                "churned": lambda: 0
            }
            
            for col, gen_default in required_cols.items():
                if col not in df_upload.columns:
                    df_upload[col] = [gen_default() for _ in range(len(df_upload))]
                    
            # Normalize specific column fields
            df_upload["customer_id"] = df_upload["customer_id"].astype(str)
            df_upload["age"] = df_upload["age"].fillna(35).astype(int)
            df_upload["income"] = df_upload["income"].fillna(50000.0).astype(float)
            df_upload["purchase_amount"] = df_upload["purchase_amount"].fillna(150.0).astype(float)
            df_upload["purchase_frequency"] = df_upload["purchase_frequency"].fillna(5).astype(int)
            df_upload["emi_amount"] = df_upload["emi_amount"].fillna(0.0).astype(float)
            df_upload["emi_tenure"] = df_upload["emi_tenure"].fillna(0).astype(int)
            df_upload["engagement_score"] = df_upload["engagement_score"].fillna(5).astype(int)
            df_upload["customer_satisfaction_score"] = df_upload["customer_satisfaction_score"].fillna(4).astype(int)
            df_upload["churned"] = df_upload["churned"].fillna(0).astype(int)
            
            # Clean db and insert records
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers") # Clear existing
            
            for idx, row in df_upload.iterrows():
                cursor.execute("""
                INSERT INTO customers (
                    customer_id, name, age, gender, location, income, product_purchased,
                    purchase_amount, purchase_frequency, emi_amount, emi_tenure, emi_status,
                    subscription_type, subscription_expiry_date, last_purchase_date,
                    engagement_score, customer_satisfaction_score, churned
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row["customer_id"]), str(row["name"]), int(row["age"]), str(row["gender"]), str(row["location"]),
                    float(row["income"]), str(row["product_purchased"]), float(row["purchase_amount"]),
                    int(row["purchase_frequency"]), float(row["emi_amount"]), int(row["emi_tenure"]),
                    str(row["emi_status"]), str(row["subscription_type"]), str(row["subscription_expiry_date"]),
                    str(row["last_purchase_date"]), int(row["engagement_score"]), int(row["customer_satisfaction_score"]),
                    int(row["churned"])
                ))
            conn.commit()
            conn.close()
            
            print(f"Successfully loaded and seeded {len(df_upload)} custom user records.")
        except Exception as e:
            print("Error uploading file:", str(e))
            
    return redirect(url_for("index"))

@app.route("/reset_data", methods=["POST"])
def reset_data():
    """
    Wipes the database and seeds it with the initial high-quality 150-record CSV dataset.
    """
    if not os.path.exists("sample_customers.csv"):
        import generate_dataset
        generate_dataset.generate_sample_dataset()
    db.init_db()
    return redirect(url_for("index"))

@app.route("/api/add_customer", methods=["POST"])
def add_customer():
    """
    Inserts a single customer account or updates an existing one (CRUD).
    """
    cust_data = request.form.to_dict()
    
    # Process inputs
    try:
        data = {
            "customer_id": cust_data.get("customer_id"),
            "name": cust_data.get("name"),
            "age": int(cust_data.get("age", 35)),
            "gender": cust_data.get("gender", "Male"),
            "location": cust_data.get("location", "Urban"),
            "income": float(cust_data.get("income", 50000.0)),
            "product_purchased": cust_data.get("product_purchased", "Electronics"),
            "purchase_amount": float(cust_data.get("purchase_amount", 100.0)),
            "purchase_frequency": int(cust_data.get("purchase_frequency", 5)),
            "emi_amount": float(cust_data.get("emi_amount", 0.0)),
            "emi_tenure": int(cust_data.get("emi_tenure", 0)),
            "emi_status": cust_data.get("emi_status", "N/A"),
            "subscription_type": cust_data.get("subscription_type", "None"),
            "subscription_expiry_date": cust_data.get("subscription_expiry_date", "N/A"),
            "last_purchase_date": cust_data.get("last_purchase_date", pd.Timestamp.now().strftime("%Y-%m-%d")),
            "engagement_score": int(cust_data.get("engagement_score", 5)),
            "customer_satisfaction_score": int(cust_data.get("customer_satisfaction_score", 4)),
            "churned": int(cust_data.get("churned", 0))
        }
        
        db.save_customer(data)
        return jsonify({"success": True, "message": "Customer saved successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/delete_customer/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """
    Removes a single customer account from the database (CRUD).
    """
    try:
        db.delete_customer(customer_id)
        return jsonify({"success": True, "message": "Customer deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/download/excel")
def download_excel():
    """
    Generates and downloads a custom formatted Excel workbook report.
    """
    df = db.load_data_from_db()
    if len(df) == 0:
        return redirect(url_for("index"))
        
    df_seg, _ = model_pipeline.run_segmentation(df)
    _, probs, _ = model_pipeline.train_classification_model(df)
    purchase_preds = model_pipeline.predict_purchase_behavior(df)
    recs = model_pipeline.generate_personalized_recommendations(df, probs, df_seg["segment"].values, purchase_preds)
    
    excel_stream = reports.generate_excel_report(df, dict(zip(df_seg["customer_id"], df_seg["segment"])), probs, recs)
    
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Customer_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

@app.route("/download/pdf")
def download_pdf():
    """
    Generates and downloads a professional, corporate-styled PDF analysis document.
    """
    df = db.load_data_from_db()
    if len(df) == 0:
        return redirect(url_for("index"))
        
    classifier_name = "Random Forest"
    df_seg, segment_stats = model_pipeline.run_segmentation(df)
    metrics, probs, importances = model_pipeline.train_classification_model(df, model_name=classifier_name)
    market_analysis = model_pipeline.run_market_analysis(df)
    
    pdf_stream = reports.generate_pdf_report(df, segment_stats, metrics, classifier_name, market_analysis)
    
    return send_file(
        pdf_stream,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Customer_Intelligence_Brief_{datetime.now().strftime('%Y%m%d')}.pdf"
    )

from datetime import datetime
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
