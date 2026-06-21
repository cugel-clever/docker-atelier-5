# Utiliser une image Python légère
FROM python:3.11-slim

# Créer un utilisateur non root
RUN useradd -m -s /bin/bash appuser
USER appuser

# Créer le répertoire d'application
WORKDIR /app

# Copier les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY app.py .

# Exposer le port
EXPOSE 5000

# Lancer l'application
CMD ["python", "app.py"]