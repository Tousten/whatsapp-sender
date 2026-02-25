# WhatsApp Bulk Sender - Auto Shop Oil Change Reminder
# Simple tool to send messages to multiple clients via WhatsApp Web
# Optional: Browser automation for auto-sending

from flask import Flask, render_template_string, request, jsonify, render_template
import os
import time
import csv
import io
import urllib.parse
import threading
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'whatsapp-sender-key')

# Store automation status
automation_status = {
    "running": False,
    "current": 0,
    "total": 0,
    "message": "",
    "logs": []
}

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
            max-width: 700px; 
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
        .toggle-section {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .toggle-section h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        .toggle-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .toggle-row:last-child {
            margin-bottom: 0;
        }
        .toggle-label {
            color: #856404;
        }
        .toggle-label strong {
            display: block;
            margin-bottom: 5px;
        }
        .toggle-label small {
            color: #b8860b;
        }
        .toggle-switch {
            position: relative;
            width: 60px;
            height: 30px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #ccc;
            border-radius: 30px;
            transition: 0.3s;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 22px;
            width: 22px;
            left: 4px;
            bottom: 4px;
            background: white;
            border-radius: 50%;
            transition: 0.3s;
        }
        input:checked + .slider {
            background: #25d366;
        }
        input:checked + .slider:before {
            transform: translateX(30px);
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
        .btn-secondary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-top: 10px;
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
        .automation-panel {
            background: #e3f2fd;
            border: 2px solid #2196f3;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .automation-panel.active {
            display: block;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .log-box {
            background: #1e1e1e;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 15px;
        }
        .log-box .error { color: #ff4444; }
        .log-box .success { color: #44ff44; }
        .log-box .info { color: #ffff44; }
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
                    <li>Escolha: Links manuais OU Automação</li>
                    <li>Clique em "Iniciar"</li>
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
                
                <div class="toggle-section">
                    <h3>⚙️ Modo de Envio</h3>
                    
                    <div class="toggle-row">
                        <div class="toggle-label">
                            <strong>🤖 Automação de Navegador</strong>
                            <small>Abre WhatsApp Web e envia automaticamente (requer computador ligado)</small>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" id="autoMode" name="autoMode">
                            <span class="slider"></span>
                        </label>
                    </div>
                    
                    <div id="autoSettings" style="display: none; margin-top: 15px; padding-top: 15px; border-top: 1px dashed #ffc107;">
                        <div class="toggle-row">
                            <div class="toggle-label">
                                <strong>⏱️ Intervalo entre mensagens</strong>
                                <small>Segundos de espera entre cada envio (evita bloqueio)</small>
                            </div>
                            <input type="number" name="delay" value="10" min="5" max="60" style="width: 80px; padding: 10px; border: 2px solid #ffc107; border-radius: 8px;">
                        </div>
                        
                        <div class="toggle-row">
                            <div class="toggle-label">
                                <strong>🖥️ Modo Headless</strong>
                                <small>Não mostra o navegador (mais rápido, mas sem visual)</small>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" name="headless" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">🚀 Gerar Links WhatsApp</button>
                <button type="button" class="btn btn-secondary" id="autoBtn" style="display: none;">🤖 Iniciar Automação</button>
            </form>
            
            <div id="results" class="results">
                <h3>🔗 Links Gerados</h3>
                <ul id="resultsList"></ul>
            </div>
            
            <div id="automationPanel" class="automation-panel">
                <h3>🤖 Painel de Automação</h3>
                <p id="autoStatus">Preparando...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill">0%</div>
                </div>
                <div class="log-box" id="logBox">
                    <div class="info">Aguardando início...</div>
                </div>
                <button type="button" class="btn" id="stopBtn" style="background: #f44336; margin-top: 15px;">⏹️ Parar Automação</button>
            </div>
        </div>
    </div>
    
    <script>
        // Toggle automation settings visibility
        document.getElementById('autoMode').addEventListener('change', function() {
            const autoSettings = document.getElementById('autoSettings');
            const submitBtn = document.getElementById('submitBtn');
            const autoBtn = document.getElementById('autoBtn');
            
            if (this.checked) {
                autoSettings.style.display = 'block';
                submitBtn.style.display = 'none';
                autoBtn.style.display = 'block';
            } else {
                autoSettings.style.display = 'none';
                submitBtn.style.display = 'block';
                autoBtn.style.display = 'none';
            }
        });
        
        // File input label update
        document.getElementById('csvFile').addEventListener('change', function(e) {
            const label = document.querySelector('.file-input-label');
            if (e.target.files.length > 0) {
                label.textContent = '📄 ' + e.target.files[0].name;
            }
        });
        
        // Generate links form
        document.getElementById('senderForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const btn = document.getElementById('submitBtn');
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
        
        // Automation button
        document.getElementById('autoBtn').addEventListener('click', async function() {
            const formData = new FormData(document.getElementById('senderForm'));
            const panel = document.getElementById('automationPanel');
            const btn = document.getElementById('autoBtn');
            
            btn.disabled = true;
            btn.textContent = '⏳ Iniciando...';
            panel.classList.add('active');
            
            try {
                const response = await fetch('/automate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    startMonitoring();
                } else {
                    alert('Erro: ' + data.error);
                    btn.disabled = false;
                    btn.textContent = '🤖 Iniciar Automação';
                }
            } catch (error) {
                alert('Erro: ' + error.message);
                btn.disabled = false;
                btn.textContent = '🤖 Iniciar Automação';
            }
        });
        
        // Stop automation
        document.getElementById('stopBtn').addEventListener('click', async function() {
            try {
                await fetch('/stop', { method: 'POST' });
                document.getElementById('autoStatus').textContent = 'Parando...';
            } catch (error) {
                console.error(error);
            }
        });
        
        // Monitor automation progress
        let monitorInterval;
        function startMonitoring() {
            monitorInterval = setInterval(async () => {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    // Update progress
                    const percent = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
                    document.getElementById('progressFill').style.width = percent + '%';
                    document.getElementById('progressFill').textContent = percent + '%';
                    document.getElementById('autoStatus').textContent = data.message;
                    
                    // Update logs
                    const logBox = document.getElementById('logBox');
                    logBox.innerHTML = data.logs.map(log => {
                        const className = log.type || 'info';
                        return `<div class="${className}">[${log.time}] ${log.message}</div>`;
                    }).join('');
                    logBox.scrollTop = logBox.scrollHeight;
                    
                    // Check if done
                    if (!data.running) {
                        clearInterval(monitorInterval);
                        document.getElementById('autoBtn').disabled = false;
                        document.getElementById('autoBtn').textContent = '🤖 Iniciar Automação';
                    }
                } catch (error) {
                    console.error(error);
                }
            }, 1000);
        }
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
    clients = parse_clients(request)
    
    if not clients:
        return jsonify({'success': False, 'error': 'Nenhum cliente encontrado. Verifique o CSV ou a lista.'})
    
    message_template = request.form.get('message', 'Olá {nome}!')
    
    links = []
    for client in clients:
        personalized_msg = message_template.replace('{nome}', client['name'])
        encoded_msg = urllib.parse.quote(personalized_msg)
        wa_link = f"https://wa.me/{client['phone']}?text={encoded_msg}"
        
        links.append({
            'name': client['name'],
            'phone': client['phone'],
            'link': wa_link,
            'message': personalized_msg
        })
    
    return jsonify({'success': True, 'links': links, 'count': len(links)})

@app.route('/automate', methods=['POST'])
def automate():
    """Start browser automation"""
    global automation_status
    
    if automation_status['running']:
        return jsonify({'success': False, 'error': 'Automação já está rodando'})
    
    clients = parse_clients(request)
    if not clients:
        return jsonify({'success': False, 'error': 'Nenhum cliente encontrado'})
    
    message_template = request.form.get('message', 'Olá {nome}!')
    delay = int(request.form.get('delay', 10))
    headless = request.form.get('headless') == 'on'
    
    # Reset status
    automation_status = {
        "running": True,
        "current": 0,
        "total": len(clients),
        "message": f"Iniciando envio para {len(clients)} clientes...",
        "logs": [{"time": time.strftime("%H:%M:%S"), "message": "Automação iniciada", "type": "info"}]
    }
    
    # Start automation in background thread
    thread = threading.Thread(
        target=run_automation,
        args=(clients, message_template, delay, headless)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

@app.route('/status')
def status():
    """Get automation status"""
    return jsonify(automation_status)

@app.route('/stop', methods=['POST'])
def stop():
    """Stop automation"""
    global automation_status
    automation_status['running'] = False
    automation_status['message'] = 'Parando automação...'
    add_log('Parando automação...', 'info')
    return jsonify({'success': True})

def parse_clients(request):
    """Parse clients from CSV or text list"""
    clients = []
    
    # Try CSV file
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
                        phone = clean_phone(phone)
                        clients.append({'name': name, 'phone': phone})
            except Exception as e:
                print(f"CSV error: {e}")
    
    # Try text list
    if not clients:
        client_list = request.form.get('clientList', '').strip()
        if client_list:
            for line in client_list.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if '-' in line:
                    parts = line.rsplit('-', 1)
                    name = parts[0].strip()
                    phone = clean_phone(parts[1].strip())
                elif ',' in line:
                    parts = line.split(',', 1)
                    name = parts[0].strip()
                    phone = clean_phone(parts[1].strip())
                else:
                    name = 'Cliente'
                    phone = clean_phone(line)
                
                if phone:
                    clients.append({'name': name, 'phone': phone})
    
    return clients

def clean_phone(phone):
    """Clean and format phone number for WhatsApp"""
    digits = ''.join(c for c in phone if c.isdigit())
    
    if digits.startswith('0'):
        digits = '55' + digits[1:]
    
    if not digits.startswith('55') and len(digits) <= 11:
        digits = '55' + digits
    
    return digits

def add_log(message, type_='info'):
    """Add log entry"""
    automation_status['logs'].append({
        "time": time.strftime("%H:%M:%S"),
        "message": message,
        "type": type_
    })
    # Keep only last 50 logs
    automation_status['logs'] = automation_status['logs'][-50:]

def run_automation(clients, message_template, delay, headless):
    """Run browser automation"""
    global automation_status
    
    try:
        # Check if selenium is available
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError:
            automation_status['running'] = False
            automation_status['message'] = 'Erro: Selenium não instalado'
            add_log('Selenium não encontrado. Instale com: pip install selenium', 'error')
            return
        
        add_log('Iniciando navegador...', 'info')
        
        # Setup Chrome options
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Try to start browser
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            add_log(f'Erro ao iniciar Chrome: {str(e)}', 'error')
            add_log('Tentando Firefox...', 'info')
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                options = FirefoxOptions()
                if headless:
                    options.add_argument('--headless')
                driver = webdriver.Firefox(options=options)
            except Exception as e2:
                automation_status['running'] = False
                automation_status['message'] = 'Erro: Navegador não encontrado'
                add_log(f'Firefox também falhou: {str(e2)}', 'error')
                return
        
        add_log('Navegador iniciado. Escaneie o QR code se necessário.', 'success')
        
        # Process each client
        for i, client in enumerate(clients):
            if not automation_status['running']:
                add_log('Automação interrompida pelo usuário', 'info')
                break
            
            automation_status['current'] = i + 1
            automation_status['message'] = f"Enviando para {client['name']}... ({i+1}/{len(clients)})"
            
            personalized_msg = message_template.replace('{nome}', client['name'])
            encoded_msg = urllib.parse.quote(personalized_msg)
            wa_link = f"https://wa.me/{client['phone']}?text={encoded_msg}"
            
            add_log(f'Abrindo chat: {client["name"]} ({client["phone"]})', 'info')
            
            try:
                driver.get(wa_link)
                
                # Wait for page to load
                time.sleep(3)
                
                # Wait for either QR code scan or chat to load
                try:
                    # Try to find the send button or text input
                    wait = WebDriverWait(driver, 30)
                    
                    # Look for the main chat input
                    input_selectors = [
                        '//div[@contenteditable="true"][@data-tab="1"]',
                        '//div[@contenteditable="true"]',
                        '[data-testid="conversation-compose-box-input"]',
                        '[data-testid="compose-box-input"]'
                    ]
                    
                    input_found = False
                    for selector in input_selectors:
                        try:
                            if selector.startswith('//'):
                                input_box = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                            else:
                                input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            input_found = True
                            break
                        except:
                            continue
                    
                    if not input_found:
                        # Might need QR code scan
                        add_log('Aguardando escaneamento do QR code...', 'info')
                        time.sleep(15)
                        continue
                    
                    # Type message
                    input_box.send_keys(personalized_msg)
                    time.sleep(1)
                    
                    # Send (Enter key)
                    input_box.send_keys(Keys.ENTER)
                    
                    add_log(f'✅ Mensagem enviada para {client["name"]}', 'success')
                    
                    # Wait before next
                    if i < len(clients) - 1:
                        add_log(f'Aguardando {delay} segundos...', 'info')
                        time.sleep(delay)
                    
                except Exception as e:
                    add_log(f'❌ Erro ao enviar para {client["name"]}: {str(e)}', 'error')
                    time.sleep(5)
                    
            except Exception as e:
                add_log(f'❌ Erro: {str(e)}', 'error')
                time.sleep(5)
        
        driver.quit()
        automation_status['running'] = False
        automation_status['message'] = f'Concluído! {automation_status["current"]}/{len(clients)} mensagens enviadas.'
        add_log('Automação finalizada', 'success')
        
    except Exception as e:
        automation_status['running'] = False
        automation_status['message'] = f'Erro: {str(e)}'
        add_log(f'Erro fatal: {str(e)}', 'error')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
