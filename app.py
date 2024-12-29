from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import paramiko

app = Flask(__name__)
app.secret_key = 'root'

# Gestion des connexions SSH
class SSHConnection:
    def __init__(self):
        self.client = None

    def connect(self, hostname, username, password):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname, username=username, password=password)

    def execute_command(self, command):
        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)
            return stdout.read().decode(), stderr.read().decode()
        return None, "No connection"

    def close(self):
        if self.client:
            self.client.close()

ssh_connection = SSHConnection()

# Routes Flask
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/connect', methods=['POST'])
def connect():
    ip = request.form['ip']
    username = request.form['username']
    password = request.form['password']

    try:
        ssh_connection.connect(ip, username, password)
        session['connected'] = True
        return redirect(url_for('terminal'))
    except Exception as e:
        return f"Erreur de connexion : {str(e)}"

@app.route('/terminal')
def terminal():
    if not session.get('connected'):
        return redirect(url_for('login'))
    return render_template('terminal.html')

@app.route('/execute', methods=['POST'])
def execute():
    try:
        # Récupérer les données JSON envoyées par le frontend
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': 'Aucune commande reçue'}), 400

        command = data['command']  # Extraire la commande
        stdout, stderr = ssh_connection.execute_command(command)

        # Retourner la réponse JSON avec stdout et stderr
        return jsonify({'stdout': stdout, 'stderr': stderr})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/disconnect')
def disconnect():
    ssh_connection.close()
    session.pop('connected', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
