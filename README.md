## SQL Optimizer Pro  
A Rule-Based SQL Query Optimizer with Automatic Rewrites and Cost Estimation

SQL Optimizer Pro is a complete rule-based SQL Query Optimization tool built using Python and Flask.  
It analyzes SQL queries, detects inefficiencies, applies safe rewrites, and estimates execution cost — similar to how real database optimizers work.






##  Project Structure
```
sql-optimizer/
│
├── app.py
├── run.bat                                 
├── Dockerfile
├── requirements.txt
├── README.md
│
├── schema_stats.py
│
├── optimizer/
│   ├── __init__.py
│   ├── parser.py
│   ├── rules.py             
│   ├── generator.py         
│   ├── cost_estimator.py

```



## Installation (Local)

Clone repo:
```
git clone https://github.com/your-name/sql-optimizer.git
cd sql-optimizer
```

Create virtual env:
```
python -m venv venv
venv/Scripts/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Run locally:
```
python app.py
```

Open:
```
http://127.0.0.1:5000
```
or 
Double-click:
```
run.bat
```
