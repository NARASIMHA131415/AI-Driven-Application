# AI-Driven Customer Intelligence & Churn Prediction Platform

A full-stack, AI-powered Customer Intelligence Platform that analyzes customer behavior, predicts future purchases, identifies churn risks, performs customer segmentation, and provides personalized recommendations using Machine Learning, Statistical Analysis, and Interactive Data Visualizations.

---

## 🚀 Core Features

1. **Customer Data Analysis**: Upload customer CSV files, analyze demographics, transactions, EMIs, subscriptions, and engagement.
2. **Customer Segmentation**: Run **K-Means** or **Hierarchical** clustering dynamically to group customers into 6 core business cohorts.
3. **Purchase Behavior Prediction**: Multi-class Random Forest for next product category and Random Forest Regressor for future spending size.
4. **Churn Forecasting & Classifiers**: Retrain and compare **Random Forest**, **Decision Tree**, **Logistic Regression**, or **XGBoost** models on the fly.
5. **Personalized Recommendations**: Dynamic cards featuring product suggestions, customized voucher codes, renewal reminders, pre-approved EMI plans, and loyalty points.
6. **Market Projections & Trends**: 6-month projected revenue, seasonal purchase trends, and product demand forecasting.
7. **Interactive Dashboard**: KPI metrics, paginated database CRUD manager, search/filters, and 7 Chart.js interactive charts.
8. **Report Generation**: Export full results as professionally-formatted **Excel files** or executive-ready **PDF briefs**.

---

## 🛠️ Local Installation & Run Commands

Ensure you have Python 3.10+ installed. Follow these commands:

1. **Extract the ZIP file** and navigate to the directory:
   ```bash
   unzip customer-intelligence-platform.zip
   cd customer-intelligence-platform
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize & Seed the Database**:
   The database will automatically initialize on server start. However, if you want to explicitly generate the sample data:
   ```bash
   python3 generate_dataset.py
   python3 db.py
   ```

5. **Start the Flask Development Server**:
   ```bash
   python3 app.py
   ```

6. **Access the application**:
   Open your browser and visit: **`http://127.0.0.1:5000`**

---

## ☁️ Deploying to Render

This repository has been fully optimized for seamless deployment to **Render** (render.com).

### Step-by-Step Deployment Guide:

1. **Upload Code to GitHub**:
   Push these project files to a new repository on your GitHub account.

2. **Log into Render**:
   Go to [Render.com](https://render.com) and sign in (link your GitHub account).

3. **Create a New Web Service**:
   * Click **New** > **Web Service**.
   * Connect your connected GitHub repository.

4. **Configure Settings on Render**:
   * **Name**: `customer-intelligence-platform`
   * **Environment**: `Python`
   * **Branch**: `main` (or whichever branch you pushed to)
   * **Build Command**: 
     ```bash
     pip install -r requirements.txt && python3 generate_dataset.py && python3 db.py
     ```
     *(This ensures the requirements are installed and the initial SQLite database is seeded!)*
   * **Start Command**: 
     ```bash
     gunicorn wsgi:app
     ```

5. **Deploy**:
   Click **Deploy Web Service**. Render will spin up the environment, build dependencies, initialize the SQLite database, and launch your platform!

---

## 📊 File Structure
```
├── app.py                  # Main Flask Web Server
├── generate_dataset.py     # Script generating 150+ realistic client records
├── db.py                   # SQLite Database initialization & CRUD interfaces
├── model_pipeline.py       # ML clustering, classification, and recommendations
├── reports.py              # PDF (ReportLab) & Excel (openpyxl) document builders
├── wsgi.py                 # Gunicorn entry point for cloud deployment
├── requirements.txt        # PIP dependencies
├── README.md               # User & Deployment guide
└── templates/
      └── index.html        # Interactive Frontend Dashboard
```
