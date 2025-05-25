from flask import Flask, render_template, request, jsonify, make_response
import csv
import re
import io
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
from Bio import SeqIO

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 郵件配置
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_DEBUG'] = True

mail = Mail(app)

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
    # 檢查當前激活的輸入方式（通過檢查哪個字段有值）
    if 'fasta_file' in request.files and request.files['fasta_file'].filename != '':
        # 處理FASTA上傳
        fasta_file = request.files['fasta_file']
        try:
            content = fasta_file.read().decode('utf-8')
            fasta_io = io.StringIO(content)
            records = list(SeqIO.parse(fasta_io, "fasta"))
            
            if not records:
                return render_template('index.html', error="FASTA檔案中沒有找到有效的序列")
            
            first_record = records[0]
            sequence = str(first_record.seq)
            
            temp_id = "UPLOAD_" + str(abs(hash(sequence)))[:8]
            protein_db[temp_id] = {
                "name": first_record.description[:50],
                "sequence": sequence,
                "pdb_id": "N/A",
                "length": len(sequence),
                "species": "Uploaded sequence"
            }
            
            return render_template('results.html', 
                               protein_id=temp_id,
                               data=protein_db[temp_id])
            
        except Exception as e:
            return render_template('index.html', 
                                error=f"處理FASTA檔案時發生錯誤: {str(e)}")
    
    elif 'query' in request.form and request.form['query'].strip():
        # 處理直接輸入
        query = request.form['query'].strip()
        
        # 判斷是UniProt ID還是序列
        if re.match(r'^[A-Z0-9]{6,10}$', query.upper()):
            # UniProt ID
            if query.upper() in protein_db:
                return render_template('results.html', 
                                   protein_id=query.upper(),
                                   data=protein_db[query.upper()])
            else:
                return render_template('index.html', 
                                    error=f"未找到 {query} 的記錄")
        elif re.match(r'^[ACDEFGHIKLMNPQRSTVWY]+$', query.upper()):
            # 蛋白質序列
            temp_id = "SEQ_" + str(abs(hash(query)))[:8]
            protein_db[temp_id] = {
                "name": "User provided sequence",
                "sequence": query.upper(),
                "pdb_id": "N/A",
                "length": len(query),
                "species": "Unknown"
            }
            return render_template('results.html', 
                               protein_id=temp_id,
                               data=protein_db[temp_id])
        else:
            return render_template('index.html', 
                                error="無效的輸入，請輸入有效的UniProt ID或蛋白質序列")
    
    # 如果兩種輸入方式都沒有提供數據
    return render_template('index.html', 
                        error="請選擇一種輸入方式並提供數據")

def generate_csv(protein_id, protein_data):
    """生成CSV文件的函數"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入標題行
    writer.writerow(['Protein ID', 'Property', 'Value'])
    
    # 寫入數據行
    writer.writerow([protein_id, 'Name', protein_data['name']])
    writer.writerow([protein_id, 'PDB ID', protein_data['pdb_id']])
    writer.writerow([protein_id, 'Length', protein_data['length']])
    writer.writerow([protein_id, 'Species', protein_data['species']])
    writer.writerow([protein_id, 'Sequence', protein_data['sequence']])
    
    return output.getvalue()

@app.route('/download_csv/<protein_id>')
def download_csv(protein_id):
    """下載CSV文件的路由"""
    if protein_id in protein_db:
        csv_data = generate_csv(protein_id, protein_db[protein_id])
        
        response = make_response(csv_data)
        response.headers['Content-Disposition'] = f'attachment; filename={protein_id}_analysis.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    return jsonify({'error': 'Protein not found'}), 404

@app.route('/send_email', methods=['POST'])
def send_email():
    """發送郵件的路由"""
    try:
        data = request.json
        protein_id = data.get('protein_id')
        email = data.get('email')
        
        # 驗證輸入
        if not protein_id or not email:
            return jsonify({'status': 'error', 'message': '缺少 protein_id 或 email'}), 400
            
        if protein_id not in protein_db:
            return jsonify({'status': 'error', 'message': '找不到指定的蛋白質'}), 404
            
        # 生成CSV
        csv_data = generate_csv(protein_id, protein_db[protein_id])
        
        # 創建郵件
        msg = Message(
            subject=f"ProteinExplorer 分析結果 - {protein_id}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email],
            body=f"附件是蛋白質 {protein_id} 的分析結果。\n\n此郵件由 ProteinExplorer 系統自動發送。"
        )
        
        # 附加CSV文件
        msg.attach(
            filename=f"{protein_id}_analysis.csv",
            content_type="text/csv",
            data=csv_data
        )
        
        # 發送郵件
        mail.send(msg)
        
        return jsonify({
            'status': 'success', 
            'message': '郵件已成功發送'
        })
        
    except Exception as e:
        app.logger.error(f"郵件發送錯誤: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error', 
            'message': f'郵件發送失敗: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)