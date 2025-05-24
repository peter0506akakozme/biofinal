from flask import Flask, render_template, request

app = Flask(__name__)

# 模擬數據庫
protein_db = {
    "P00533": {
        "name": "EGFR",
        "sequence": "MTEITAAMVK...",  # 截斷顯示
        "pdb_id": "1IVO",
        "length": 1210,
        "species": "Homo sapiens"
    },
    "P69905": {
        "name": "Hemoglobin",
        "sequence": "MVLSPADKTN...",
        "pdb_id": "1HHO",
        "length": 147,
        "species": "Human"
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query').strip().upper()
    if query in protein_db:
        return render_template('results.html', 
                           protein_id=query,
                           data=protein_db[query])
    return render_template('index.html', 
                        error=f"未找到 {query} 的記錄")


if __name__ == '__main__':
    app.run(debug=True)