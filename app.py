# app.py
from flask import Flask, request, jsonify
import torch
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Configuration de la base de données via variables d'environnement
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "predictions_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Modèle "toy" : y = 2x + 1
def predict(x):
    x_tensor = torch.tensor([x], dtype=torch.float32)
    y = 2 * x_tensor + 1
    return y.item()

# Connexion à la base de données
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        app.logger.error(f"Erreur de connexion à la base : {e}")
        raise

# Initialisation de la table si elle n'existe pas
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            x FLOAT NOT NULL,
            y FLOAT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Route /predict : applique le modèle, enregistre dans la base
@app.route('/predict', methods=['GET'])
def predict_route():
    try:
        x = request.args.get('x', type=float)
        if x is None:
            return jsonify({'error': 'Paramètre "x" manquant'}), 400

        y = predict(x)

        # Enregistrer dans la base
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO predictions (x, y) VALUES (%s, %s)",
            (x, y)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'x': x, 'y': y, 'message': 'Prédiction enregistrée dans la base'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route /history : retourne les 10 dernières prédictions
@app.route('/history', methods=['GET'])
def history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, x, y, timestamp FROM predictions ORDER BY timestamp DESC LIMIT 10"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        predictions = [
            {
                'id': row[0],
                'x': row[1],
                'y': row[2],
                'timestamp': row[3].isoformat()
            }
            for row in rows
        ]
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route racine
@app.route('/')
def home():
    return """
    <h1>Bienvenue sur l'API de prédiction</h1>
    <p>Utilisez <code>/predict?x=5</code> pour obtenir y = 2x + 1.</p>
    <p>Consultez <code>/history</code> pour voir les dernières prédictions.</p>
    <p>La base de données est gérée par PostgreSQL via Docker Compose.</p>
    """

# Lancement du serveur
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
