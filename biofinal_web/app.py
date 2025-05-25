from flask import Flask, render_template, request, jsonify, make_response
import csv
import re
import io
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
from Bio import SeqIO
import joblib
from utils import extract_aac_features  # 請換成你的實際模組
import hashlib
import subprocess
import tempfile

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

# 載入模型與編碼器
model = joblib.load("svm_model_AAC.pkl")
label_encoder = joblib.load("label_encoder_AAC.pkl")

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

    def predict_family(seq):
        features = extract_aac_features(seq)
        prediction = model.predict([features])[0]
        return label_encoder.inverse_transform([prediction])[0]

    # 檢查是否為檔案上傳
    if 'fasta_file' in request.files and request.files['fasta_file'].filename != '':
        fasta_file = request.files['fasta_file']
        try:
            content = fasta_file.read().decode('utf-8')
            fasta_io = io.StringIO(content)
            records = list(SeqIO.parse(fasta_io, "fasta"))

            if not records:
                return render_template('index.html', error="FASTA檔案中沒有找到有效的序列")
            
            first_record = records[0]
            sequence = str(first_record.seq).upper()
            family = predict_family(sequence)

            temp_id = "UPLOAD_" + str(abs(hash(sequence)))[:8]
            protein_db[temp_id] = {
                "name": first_record.description[:50],
                "sequence": sequence,
                "pdb_id": family,  # ✅ 用預測家族取代 pdb_id
                "length": len(sequence),
                "species": "Uploaded sequence"
            }

            return render_template('results.html', 
                                   protein_id=temp_id,
                                   data=protein_db[temp_id])

        except Exception as e:
            return render_template('index.html', error=f"處理FASTA檔案時發生錯誤: {str(e)}")

    # 檢查是否為文字輸入
    elif 'query' in request.form and request.form['query'].strip():
        query = request.form['query'].strip().upper()

        if re.match(r'^[A-Z0-9]{6,10}$', query):
            # UniProt ID
            if query in protein_db:
                return render_template('results.html',
                                       protein_id=query,
                                       data=protein_db[query])
            else:
                return render_template('index.html', error=f"未找到 {query} 的記錄")
        elif re.match(r'^[ACDEFGHIKLMNPQRSTVWY]+$', query):
            # 蛋白質序列
            family = predict_family(query)

            temp_id = "SEQ_" + str(abs(hash(query)))[:8]
            protein_db[temp_id] = {
                "name": "User provided sequence",
                "sequence": query,
                "pdb_id": family,  # ✅ 用預測家族取代 pdb_id
                "length": len(query),
                "species": "Unknown"
            }

            return render_template('results.html',
                                   protein_id=temp_id,
                                   data=protein_db[temp_id])
        else:
            return render_template('index.html', error="無效的輸入，請輸入有效的UniProt ID或蛋白質序列")

    return render_template('index.html', error="請選擇一種輸入方式並提供數據")

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

def generate_weblogo_image(sequence, output_path):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_fasta:
        temp_fasta.write(">sequence\n")
        temp_fasta.write(sequence + "\n")
        temp_fasta_path = temp_fasta.name

    # 使用 weblogo CLI 產生 PNG
    with open(output_path, "wb") as out_img, open(temp_fasta_path, "rb") as in_fasta:
        subprocess.run(
            ["weblogo", "--format", "PNG"],
            stdin=in_fasta,
            stdout=out_img,
            check=True
        )

    os.remove(temp_fasta_path)

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
    try:
        data = request.json
        protein_id = data.get('protein_id')
        email = data.get('email')
        
        if not protein_id or not email:
            return jsonify({'status': 'error', 'message': '缺少 protein_id 或 email'}), 400
            
        if protein_id not in protein_db:
            return jsonify({'status': 'error', 'message': '找不到指定的蛋白質'}), 404

        # 生成 CSV
        csv_data = generate_csv(protein_id, protein_db[protein_id])

        # 產生 WebLogo 圖檔
        sequence = protein_db[protein_id]["sequence"]
        logo_path = f"{protein_id}_weblogo.png"
        generate_weblogo_image(sequence, logo_path)

        # 建立郵件
        msg = Message(
            subject=f"ProteinExplorer Result - {protein_id}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email],
            body=f"Attached is your analysis result and WebLogo image for {protein_id}."
        )

        # 附加 CSV
        msg.attach(
            filename=f"{protein_id}_analysis.csv",
            content_type="text/csv",
            data=csv_data
        )

        # 附加 WebLogo 圖
        with open(logo_path, "rb") as f:
            msg.attach(
                filename=logo_path,
                content_type="image/png",
                data=f.read()
            )

        os.remove(logo_path)

        # 寄送郵件
        mail.send(msg)

        return jsonify({'status': 'success', 'message': '郵件已成功發送！'})

    except Exception as e:
        app.logger.error(f"郵件發送錯誤: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'郵件發送失敗: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)