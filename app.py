from flask import Flask, request, render_template_string, jsonify
from optimizer import analyze_query
from schema_stats import SCHEMA_STATS

app = Flask(__name__)

# --- ADVANCED UI TEMPLATE (DARK MODE + TABS + SYNTAX HIGHLIGHTING) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SQL Optimizer Pro</title>

    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">

    <!-- PrismJS for SQL Syntax Highlighting -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet"/>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sql.min.js"></script>

    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            background-color: #0f1217;
            color: #e6e6e6;
            overflow-x: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 240px;
            background: #181c22;
            height: 100vh;
            padding: 25px 20px;
            position: fixed;
            top: 0;
            left: 0;
            border-right: 1px solid #222831;
        }
        .sidebar h2 {
            font-size: 1.4rem;
            color: #00d4ff;
            margin-bottom: 25px;
        }
        .sidebar a {
            display: block;
            padding: 10px 0;
            font-size: 1rem;
            text-decoration: none;
            color: #c9c9c9;
        }
        .sidebar a:hover {
            color: #00d4ff;
        }

        /* Main content */
        .main {
            margin-left: 260px;
            padding: 40px 50px;
        }

        .main h1 {
            font-size: 2rem;
            margin-bottom: 20px;
        }

        textarea {
            width: 100%;
            height: 180px;
            background: #14181f;
            border: 1px solid #2d3748;
            color: #e6e6e6;
            font-size: 15px;
            padding: 12px;
            border-radius: 8px;
            resize: vertical;
            margin-top: 10px;
        }

        button {
            padding: 12px 20px;
            background: #00d4ff;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            font-weight: 600;
            margin-top: 15px;
        }
        button:hover {
            background: #00b8df;
        }

        .toggle-box {
            margin-top: 15px;
            margin-bottom: 10px;
            font-size: 1rem;
        }

        /* Cards */
        .card {
            background: #181c22;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #232931;
            margin-top: 25px;
        }

        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid #2c3440;
            margin-top: 30px;
        }
        .tab {
            padding: 12px 25px;
            cursor: pointer;
            font-weight: 600;
            color: #b7b7b7;
            border-bottom: 2px solid transparent;
        }
        .tab.active {
            color: #00d4ff;
            border-bottom: 2px solid #00d4ff;
        }

        .tab-content {
            display: none;
            margin-top: 20px;
        }
        .tab-content.active {
            display: block;
        }

        /* Code blocks */
        pre {
            background: #14181f;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #2d3748;
            white-space: pre-wrap;
            font-size: 0.9rem;
        }

        .copy-btn {
            float: right;
            margin-bottom: 8px;
            padding: 6px 12px;
            background: #00d4ff;
            border-radius: 6px;
            cursor: pointer;
            border: none;
            color: #000;
        }

    </style>
</head>

<body>

<div class="sidebar">
    <h2>SQL Optimizer Pro</h2>
    <a href="#">Analyzer</a>
    <a href="#">Rules</a>
    <a href="#">API Docs</a>
    <a href="#">About</a>
</div>

<div class="main">
    <h1>Analyze & Optimize SQL</h1>

    <form method="POST">
        <textarea name="query" placeholder="SELECT * FROM users WHERE age > 25;">{{ query }}</textarea>

        <div class="toggle-box">
            <label>
                <input type="checkbox" name="apply_rewrites" {% if apply_rewrites %}checked{% endif %}> Apply Safe Rewrites
            </label>
        </div>

        <button type="submit">Run Optimization</button>
    </form>

    {% if result %}
    <div class="tabs">
        <div class="tab active" onclick="showTab(0)">Suggestions</div>
        <div class="tab" onclick="showTab(1)">Parsed</div>
        <div class="tab" onclick="showTab(2)">Rewrites</div>
        <div class="tab" onclick="showTab(3)">Cost</div>
    </div>

    <!-- Suggestions -->
    <div class="tab-content active">
        <div class="card">
            <h3>Suggestions</h3>
            {% if result.suggestions %}
                <ul>
                    {% for s in result.suggestions %}
                    <li>{{ s }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>No major suggestions found! 🎉</p>
            {% endif %}
        </div>
    </div>

    <!-- Parsed -->
    <div class="tab-content">
        <div class="card">
            <h3>Parsed Query</h3>
            <pre>{{ result.parsed | tojson(indent=2) }}</pre>
        </div>
    </div>

    <!-- Rewrites -->
    <div class="tab-content">
        <div class="card">
            <h3>Optimized Query</h3>

            {% if apply_rewrites %}
                <button class="copy-btn" onclick="copyOpt()">Copy</button>
                <pre id="opt_sql" class="language-sql"><code>{{ result.optimized_query }}</code></pre>
            {% else %}
                <p>Safe rewrites disabled.</p>
            {% endif %}

            <h3>Applied Rewrites</h3>
            {% if result.applied_rewrites %}
            <ul>
                {% for r in result.applied_rewrites %}
                <li>{{ r }}</li>
                {% endfor %}
            </ul>
            {% else %}
                <p>No rewrites applied.</p>
            {% endif %}
        </div>
    </div>

    <!-- Cost -->
    <div class="tab-content">
        <div class="card">
            <h3>Cost Analysis</h3>
            <p><strong>Before:</strong> {{ result.cost_before }}</p>
            <p><strong>After:</strong> {{ result.cost_after }}</p>
        </div>
    </div>

    {% endif %}
</div>

<script>
function showTab(i) {
    const tabs = document.querySelectorAll(".tab");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach((t, idx) => {
        t.classList.toggle("active", idx === i);
        contents[idx].classList.toggle("active", idx === i);
    });
}

function copyOpt() {
    let txt = document.getElementById("opt_sql").innerText;
    navigator.clipboard.writeText(txt);
    alert("Optimized SQL copied!");
}
</script>

</body>
</html>
"""


# ---------------- HOME ROUTE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    query = ""
    result = None
    apply_rewrites = False

    if request.method == "POST":
        query = request.form.get("query", "")
        apply_rewrites = request.form.get("apply_rewrites") == "on"

        analysis = analyze_query(query, SCHEMA_STATS)

        if not apply_rewrites:
            analysis["optimized_query"] = "Safe rewrites disabled."
            analysis["applied_rewrites"] = []

        result = analysis

    return render_template_string(
        HTML_PAGE,
        query=query,
        result=result,
        apply_rewrites=apply_rewrites
    )

# ---------------- API ROUTE ----------------
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True)
    q = data.get("query", "")
    apply_rewrites = data.get("apply_rewrites", False)

    res = analyze_query(q, SCHEMA_STATS)

    if not apply_rewrites:
        res["optimized_query"] = None
        res["applied_rewrites"] = []

    return jsonify(res)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
