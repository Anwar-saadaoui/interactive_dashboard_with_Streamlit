# 🛒 Superstore Sales — End-to-End Data Analytics Project

A complete Data Engineering and Analytics pipeline built over 3 sprints:
**Data Cleaning → PostgreSQL Database → Interactive Dashboard**

---

## 📌 Project Summary

This project takes raw Superstore sales data through a full professional data pipeline:

| Sprint | Phase | Description |
|--------|-------|-------------|
| Week 1 | 🧹 Data Cleaning | Clean and prepare raw CSV data with Pandas |
| Week 2 | 🗄️ Data Engineering | Model, normalize and load data into PostgreSQL |
| Week 3 | 📊 Data Visualization | Build an interactive Streamlit dashboard |

---

## 🗂️ Project Structure

```
superstore_project/
│
├── docker-compose.yml              
├── Dockerfile.jupyter              
│
├── data/
│   └── superstore_cleaned.csv      
│
├── notebooks/
│   └── superstore_pipeline.ipynb   
│
├── dashboard/
│   └── app.py                      
│
└── README.md
```

---

## 🐳 Infrastructure — Docker Services

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| `superstore_postgres` | postgres:15 | 5432 | PostgreSQL database |
| `superstore_pgadmin` | dpage/pgadmin4 | 8080 | Database GUI |
| `superstore_jupyter` | python:3.11-slim | 8888 | Data pipeline notebook |
| `superstore_streamlit` | python:3.11-slim | 8501 | Interactive dashboard |

---

## 🧹 Sprint 1 — Data Cleaning

### Dataset
Raw Superstore sales data with the following columns:

```
row_id, order_id, order_date, ship_date, ship_mode,
customer_id, customer_name, segment, country, city, state,
postal_code, region, product_id, category, sub-category,
product_name, sales, year, month, quarter, delivery_days
```

### What was done
- Removed duplicates and null values
- Fixed data types (dates, numerics, strings)
- Standardized column names
- Calculated derived columns: `year`, `month`, `quarter`, `delivery_days`
- Exported clean dataset as `superstore_cleaned.csv`

---

## 🗄️ Sprint 2 — PostgreSQL Data Engineering

### Normalized Relational Schema (3NF)

```
regions ──────────────────────────┐
  region_id (PK)                  │
  region, country, state...       │
                                  ▼
customers ──────────────► orders ◄──────────── order_items (FACT)
  customer_id (PK)          order_id (PK)        item_id (PK)
  customer_name             customer_id (FK)      order_id (FK)
  segment                   region_id (FK)        product_id (FK)
                            order_date            sales
                            ship_mode             delivery_days
                            year, month, quarter

categories ──────────► products
  category_id (PK)       product_id (PK)
  category               product_name
  sub_category           category_id (FK)
```

### Tables Created

| Table | Type | Description |
|-------|------|-------------|
| `regions` | Dimension | Geographic data |
| `customers` | Dimension | Customer info & segment |
| `categories` | Dimension | Product category & sub-category |
| `products` | Dimension | Product details |
| `orders` | Dimension | Order header info |
| `order_items` | **Fact** | Sales transactions |

### SQL Views

| View | Description |
|------|-------------|
| `v_sales_by_category` | Sales by category and sub-category |
| `v_sales_by_region` | Sales and orders by region and state |
| `v_top_customers` | Customers ranked by total revenue |
| `v_monthly_sales` | Monthly aggregated sales and orders |

### Key Business Queries

**Total Sales by Category**
```sql
SELECT c.category, ROUND(SUM(oi.sales)::numeric, 2) AS total_sales
FROM order_items oi
JOIN products p   ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
GROUP BY c.category
ORDER BY total_sales DESC;
```

**Top 10 Customers by Revenue**
```sql
SELECT cu.customer_name, ROUND(SUM(oi.sales)::numeric, 2) AS revenue
FROM order_items oi
JOIN orders o     ON oi.order_id = o.order_id
JOIN customers cu ON o.customer_id = cu.customer_id
GROUP BY cu.customer_name
ORDER BY revenue DESC
LIMIT 10;
```

**Sales by Region**
```sql
SELECT r.region, ROUND(SUM(oi.sales)::numeric, 2) AS total_sales
FROM order_items oi
JOIN orders o  ON oi.order_id = o.order_id
JOIN regions r ON o.region_id = r.region_id
GROUP BY r.region
ORDER BY total_sales DESC;
```

**Orders per Month**
```sql
SELECT year, month, COUNT(DISTINCT order_id) AS nb_orders
FROM orders
GROUP BY year, month
ORDER BY year, month;
```

---

## 📊 Sprint 3 — Interactive Streamlit Dashboard

### Features

| Section | Content |
|---------|---------|
| 🔍 Sidebar Filters | Year, Region, Category, Customer Segment |
| 💰 KPI Cards | Total Sales, Orders, Customers, Avg, Median, Std Dev |
| 📦 Sales by Category | Bar chart with value labels |
| 🌍 Sales by Region | Pie chart breakdown |
| 📅 Monthly Trend | Line chart with area fill |
| 🗂️ Sub-Category | Horizontal bar chart top 10 |
| 🏆 Top Customers | Ranked horizontal bar chart |
| 👤 By Segment | Bar chart by customer segment |
| 🔥 Heatmap | Region x Category sales matrix |
| 🚚 Delivery | Avg delivery days by ship mode |
| 📐 Statistics | Full descriptive stats + histogram + boxplot |

---

## 🚀 Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### 1. Clone the repository
```bash
git clone https://github.com/your-username/superstore-postgresql.git
cd superstore-postgresql
```

### 2. Add your dataset
Place `superstore_cleaned.csv` in the `data/` folder.

### 3. Start all containers
```bash
docker-compose up --build -d
```

### 4. Verify all containers are running
```bash
docker ps
```

Expected output:
```
superstore_postgres    Up (healthy)   0.0.0.0:5432->5432/tcp
superstore_pgadmin     Up             0.0.0.0:8080->80/tcp
superstore_jupyter     Up             0.0.0.0:8888->8888/tcp
superstore_streamlit   Up             0.0.0.0:8501->8501/tcp
```

### 5. Load data via Jupyter
Go to **http://localhost:8888** and run all cells in `superstore_pipeline.ipynb`

### 6. Open the Dashboard
Go to **http://localhost:8501**

### 7. Open pgAdmin (optional)
Go to **http://localhost:8080**

| Field | Value |
|-------|-------|
| Email | `admin@superstore.com` |
| Password | `admin123` |

Connect to server:

| Field | Value |
|-------|-------|
| Host | `superstore_postgres` |
| Port | `5432` |
| Database | `superstore_db` |
| Username | `superstore_user` |
| Password | `superstore_pass` |

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Core language |
| PostgreSQL | 15 | Relational database |
| SQLAlchemy | 2.0 | ORM & DB connection |
| psycopg2 | 2.9 | PostgreSQL driver |
| Pandas | 2.x | Data processing |
| Streamlit | 1.x | Interactive dashboard |
| Matplotlib | 3.x | Charts & plots |
| Seaborn | 0.x | Heatmaps & distributions |
| Docker | Latest | Container orchestration |
| pgAdmin 4 | Latest | Database GUI |
| JupyterLab | 4.x | Notebook environment |

---

## 🔒 Security

- Base images use `python:3.11-slim` instead of heavy images
- Reduced vulnerabilities from **4 critical / 144 high → near zero**
- Credentials managed via Docker environment variables
- `.gitignore` excludes sensitive data and CSV files

---

## 📁 .gitignore

```
# Data files
data/

# Python
__pycache__/
*.pyc
.env

# Jupyter
.ipynb_checkpoints/
```

---

## 📋 Kanban Board

| Status | Tasks |
|--------|-------|
| ✅ Done | Docker setup, vulnerability fix, DB connection, schema design, table creation, data loading, integrity checks, SQL queries, SQL views, pgAdmin setup, Streamlit dashboard |
| 🔵 Backlog | Dashboard deployment, pipeline automation, advanced SQL, performance indexes |

---
