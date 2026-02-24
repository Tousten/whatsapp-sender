# WhatsApp Bulk Sender - Auto Shop Oil Change Reminder
# Simple tool to send messages to multiple clients via WhatsApp Web

from flask import Flask, render_template_string, request, jsonify
import os
import time
import csv
import io
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'whatsapp-sender-key')

# HTML Template for the tool
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Bulk Sender - Oficina</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); 
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            padding: 20px; 
        }
        .container { 
            width: 100%; 
            max-width: 600px; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 25px 80px rgba(0,0,0,0.3); 
            overflow: hidden; 
        }
        .header { 
            background: #075e54; 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 1.8rem; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 8px; 
            color: #333; 
            font-weight: 600; 
        }
        .form-group textarea, 
        .form-group input[type="text"] { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e0e0e0; 
            border-radius: 12px; 
            font-size: 1rem; 
            resize: vertical; 
        }
        .form-group textarea:focus, 
        .form-group input:focus { 
            outline: none; 
            border-color: #25d366; 
        }
        .form-group small { 
            display: block; 
            margin-top: 5px; 
            color: #666; 
        }
        .csv-section {
            background: #f0f2f5;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .csv-section h3 {
            color: #075e54;
            margin-bottom: 15px;
        }
        .csv-example {
            background: white;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            color: #333;
            margin-bottom: 15px;
            border-left: 4px solid #25d366;
        }
        .file-input-wrapper {
            position: relative;
            overflow: hidden;
            display: inline-block;
            width: 100%;
        }
        .file-input-wrapper input[type=file] {
            position: absolute;
            left: -9999px;
        }
        .file-input-label {
            display: block;
            padding: 15px;
            background: white;
            border: 2px dashed #25d366;
            border-radius: 12px;
            text-align: center;
            color: #075e54;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-input-label:hover {
            background: #e8f5e9;
        }
        .btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(37, 211, 102, 0.3);
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .results {
            margin-top: 20px;
            padding: 20px;
            border-radius: 12px;
            display: none;
        }
        .results.success { background: #e8f5e9; border: 2px solid #4caf50; }
        .results.error { background: #ffebee; border: 2px solid #f44336; }
        .results h3 { margin-bottom: 10px; }
        .results ul { list-style: none; }
        .results li { padding: 8px 0; border-bottom: 1px solid #ddd; }
        .results li:last-child { border-bottom: none; }
        .status-success { color: #4caf50; }
        .status-error { color: #f44336; }
        .instructions {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .instructions h4 { color: #856404; margin-bottom: 10px; }
        .instructions ol { margin-left: 20px; color: #856404; }
        .instructions li { margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 WhatsApp Bulk Sender</h1>
            <p>Envie mensagens para múltiplos clientes</p>
        </div>
        <div class="content">
            <div class="instructions">
                <h4>⚠️ Como usar:</h4>
                <ol>
                    <li>Prepare uma planilha CSV com: nome, telefone</li>
                    <li>Escreva sua mensagem (use {nome} para personalizar)</li>
                    <li>Clique em "Gerar Links"</li>
                    <li>Abra cada link no WhatsApp Web</li>
                </ol>
            </div>
            
            <form id="senderForm" enctype="multipart/form-data">
                <div class="csv-section">
                    <h3>📁 Clientes (CSV)</h3>
                    <div class="csv-example">
                        nome,telefone<br>
                        João Silva,5511999999999<br>
                        Maria Santos,5511888888888
                    </div>
                    <div class="file-input-wrapper">
                        <input type="file" id="csvFile" name="csvFile" accept=".csv,.txt">
                        <label for="csvFile" class="file-input-label">
                            📎 Clique para selecionar arquivo CSV
                        </label>
                    </div>
                    <small>Ou cole os números abaixo (um por linha):</small>
                </div>
                
                <div class="form-group">
                    <label>📋 Lista de Clientes (alternativo)</label>
                    <textarea id="clientList" name="clientList" rows="5" placeholder="João Silva - 5511999999999
Maria Santos - 5511888888888"></textarea>
                </div>
                
                <div class="form-group">
                    <label>💬 Mensagem</label>
                    <textarea id="message" name="message" rows="6" placeholder="Olá {nome}!&#10;&#10;Passando para lembrar que está na hora da troca de óleo do seu veículo.&#10;&#10;Agende conosco!&#10;&#10;Oficina XYZ">Olá {nome}!

Passando para lembrar que está na hora da troca de óleo do seu veículo.

Agende conosco!

Oficina XYZ</textarea>
                    <small>Use {nome} para inserir o nome do cliente automaticamente</small>
                </div>
                
                <button type="submit" class="btn">🚀 Gerar Links WhatsApp</button>
            </form>
            
            <div id="results" class="results">
                <h3>🔗 Links Gerados</h3>
                <ul id="resultsList"></ul>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('csvFile').addEventListener('change', function(e) {
            const label = document.querySelector('.file-input-label');
            if (e.target.files.length > 0) {
                label.textContent = '📄 ' + e.target.files[0].name;
            }
        });
        
        document.getElementById('senderForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const btn = document.querySelector('.btn');
            btn.disabled = true;
            btn.textContent = '⏳ Processando...';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                const resultsDiv = document.getElementById('results');
                const resultsList = document.getElementById('resultsList');
                
                resultsList.innerHTML = '';
                
                if (data.success && data.links.length > 0) {
                    data.links.forEach(item => {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <strong>${item.name}</strong> - 
                            <a href="${item.link}" target="_blank" class="status-success">Abrir WhatsApp</a>
                            <br><small style="color:#666">${item.phone}</small>
                        `;
                        resultsList.appendChild(li);
                    });
                    resultsDiv.className = 'results success';
                    resultsDiv.style.display = 'block';
                } else {
                    resultsList.innerHTML = '<li class="status-error">❌ ' + (data.error || 'Nenhum cliente encontrado') + '</li>';
                    resultsDiv.className = 'results error';
                    resultsDiv.style.display = 'block';
                }
            } catch (error) {
                alert('Erro: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Gerar Links WhatsApp';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_links():
    """Generate WhatsApp click-to-chat links for all clients"""
    clients = []
    
    # Try to read CSV file
    if 'csvFile' in request.files:
        file = request.files['csvFile']
        if file.filename:
            try:
                stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
                csv_reader = csv.DictReader(stream)
                for row in csv_reader:
                    name = row.get('nome', row.get('name', '')).strip()
                    phone = row.get('telefone', row.get('phone', row.get('numero', ''))).strip()
                    if name and phone:
                        # Clean phone number
                        phone = clean_phone(phone)
                        clients.append({'name': name, 'phone': phone})
            except Exception as e:
                return jsonify({'success': False, 'error': f'Erro no CSV: {str(e)}'})
    
    # Try to parse text list
    if not clients:
        client_list = request.form.get('clientList', '').strip()
        if client_list:
            for line in client_list.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Try to extract name and phone
                if '-' in line:
                    parts = line.rsplit('-', 1)
                    name = parts[0].strip()
                    phone = clean_phone(parts[1].strip())
                elif ',' in line:
                    parts = line.split(',', 1)
                    name = parts[0].strip()
                    phone = clean_phone(parts[1].strip())
                else:
                    # Assume it's just a phone number
                    name = 'Cliente'
                    phone = clean_phone(line)
                
                if phone:
                    clients.append({'name': name, 'phone': phone})
    
    if not clients:
        return jsonify({'success': False, 'error': 'Nenhum cliente encontrado. Verifique o CSV ou a lista.'})
    
    # Get message template
    message_template = request.form.get('message', 'Olá {nome}!')
    
    # Generate links
    links = []
    for client in clients:
        # Personalize message
        personalized_msg = message_template.replace('{nome}', client['name'])
        
        # Create WhatsApp click-to-chat link
        # Format: https://wa.me/PHONE?text=MESSAGE
        encoded_msg = urllib.parse.quote(personalized_msg)
        wa_link = f"https://wa.me/{client['phone']}?text={encoded_msg}"
        
        links.append({
            'name': client['name'],
            'phone': client['phone'],
            'link': wa_link,
            'message': personalized_msg
        })
    
    return jsonify({'success': True, 'links': links, 'count': len(links)})

def clean_phone(phone):
    """Clean and format phone number for WhatsApp"""
    # Remove all non-digits
    digits = ''.join(c for c in phone if c.isdigit())
    
    # If starts with 0, replace with 55 (Brazil)
    if digits.startswith('0'):
        digits = '55' + digits[1:]
    
    # If doesn't start with country code, add 55
    if not digits.startswith('55') and len(digits) <= 11:
        digits = '55' + digits
    
    return digits

@app.route('/api/send', methods=['POST'])
def api_send():
    """API endpoint for programmatic access"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    clients = data.get('clients', [])
    message = data.get('message', '')
    
    if not clients or not message:
        return jsonify({'success': False, 'error': 'Clients and message required'})
    
    links = []
    for client in clients:
        name = client.get('name', 'Cliente')
        phone = clean_phone(client.get('phone', ''))
        
        if phone:
            personalized_msg = message.replace('{nome}', name)
            encoded_msg = urllib.parse.quote(personalized_msg)
            wa_link = f"https://wa.me/{phone}?text={encoded_msg}"
            
            links.append({
                'name': name,
                'phone': phone,
                'link': wa_link
            })
    
    return jsonify({'success': True, 'links': links, 'count': len(links)})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
