import bcrypt
from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import json

class MonHandler(BaseHTTPRequestHandler):
    # configuration de la base de données avec mysql
    def __init__(self, *args, **kwargs):
        self.db_config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',  
            'database': 'streaming',
            'port': 3306,
            'auth_plugin': 'mysql_native_password'
        }
        super().__init__(*args, **kwargs)

    # test de la connectivité a la base de données et accès aux exceptions
    def execute_query(self, query, params=()):
        try:
            #connection à la base de données
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        # cpture de l'erreur lors de la connexion
        except Exception as e:
            print(f"Erreur MySQL: {e}")
            return None
        # fermeture de la connexion
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    # Gestion des messages serveur lors de l'exécution des requetes et gestion des différentes route
    def do_GET(self):
        try:
            print(f"Requête reçue pour: {self.path}")  # Log de débogage
            # Gestion de la page d'accueil
            if self.path == '/' or self.path == '/index.html':
                # Utilisation d'un chemin absolu
                with open('c:/Users/kimmich911/Desktop/streaming/index.html', 'rb') as file:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(file.read())
                    return

            # Gestion des fichiers dans /views
            elif self.path.startswith('/views/') or self.path.startswith('views/'):
                # Utilisation d'un chemin absolu
                file_path = f'c:/Users/kimmich911/Desktop/streaming{self.path}'
                with open(file_path, 'rb') as file:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(file.read())
                    return

            # Gestion des fichiers images
            elif self.path.startswith('/assets/') or self.path.startswith('assets/'):
                try:
                    # Chemin absolu vers le dossier assets
                    file_path = f'c:/Users/kimmich911/Desktop/streaming{self.path}'
                    print(f"Tentative d'accès au fichier: {file_path}")  # Debug log
                    
                    with open(file_path, 'rb') as file:
                        self.send_response(200)
                        # Définir le type MIME correct. toutes les extensions d'image pris en compte
                        if self.path.endswith(('.jpg', '.jpeg')):
                            self.send_header('Content-type', 'image/jpeg')
                        elif self.path.endswith('.png'):
                            self.send_header('Content-type', 'image/png')
                        elif self.path.endswith('.gif'):
                            self.send_header('Content-type', 'image/gif')
                        elif self.path.endswith('.ico'):
                            self.send_header('Content-type', 'image/x-icon')
                        else:
                            self.send_header('Content-type', 'application/octet-stream')
                        
                        self.end_headers()
                        self.wfile.write(file.read())
                        return
                        
                except Exception as e:
                    print(f"Erreur lors de l'accès au fichier: {e}")
                    self.send_error(404)
                    return

            elif self.path.startswith('/api/'):
                # Vos routes API existantes
                if self.path == '/api/users':
                    results = self.execute_query("SELECT * FROM utilisateur")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(results or []).encode())
                    return

        except Exception as e:
            print(f"Erreur: {str(e)}")
            self.send_error(404, f"Fichier non trouvé: {str(e)}")

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Il faut d'abord envoyer le code de réponse avant les headers
            if self.path == '/api/register':
                try:
                    name = data['name']
                    email = data['email']
                    password = data['password']
                    
                    # Hachage du mot de passe
                    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    
                    check_query = "SELECT * FROM utilisateurs WHERE name = %s OR email = %s"
                    exists = self.execute_query(check_query, (name, email))

                    if exists:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": False,
                            "message": "Utilisateur ou email déjà existant"
                        }).encode())
                        return

                    # Insérer le nouvel utilisateur avec le mot de passe haché
                    insert_query = "INSERT INTO utilisateurs (name, email, password) VALUES (%s, %s, %s)"
                    conn = mysql.connector.connect(**self.db_config)
                    cursor = conn.cursor()
                    cursor.execute(insert_query, (name, email, hashed))
                    conn.commit()

                    self.send_response(201)  # Created
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "message": "Inscription réussie"
                    }).encode())

                except Exception as e:
                    print(f"Erreur serveur: {str(e)}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "message": "Erreur serveur: " + str(e)
                    }).encode())
                finally:
                    if 'conn' in locals() and conn.is_connected():
                        cursor.close()
                        conn.close()

            elif self.path == '/api/login':
                try:
                    name = data['name']
                    password = data['password']

                    # Récupérer l'utilisateur et son mot de passe haché
                    query = "SELECT * FROM utilisateurs WHERE name = %s"
                    result = self.execute_query(query, (name,))

                    is_valid = False
                    if result and len(result) > 0:
                        stored_hash = result[0]['password'].encode('utf-8')
                        is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash)

                    self.send_response(200 if is_valid else 401)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()

                    if is_valid:
                        self.wfile.write(json.dumps({
                            "success": True,
                            "message": "Connexion réussie"
                        }).encode())
                    else:
                        self.wfile.write(json.dumps({
                            "success": False,
                            "message": "Nom d'utilisateur ou mot de passe incorrect"
                        }).encode())

                except Exception as e:
                    print(f"Erreur serveur: {str(e)}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "message": "Erreur serveur: " + str(e)
                    }).encode())

        except Exception as e:
            print(f"Erreur de parsing: {str(e)}")
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": "Erreur de requête: " + str(e)
            }).encode())

if __name__ == '__main__':
    server = None
    try:
        # Configuration de la base de données
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'streaming'
        }
        
        # Test de la connexion
        conn = mysql.connector.connect(**config)
        print("Connexion MySQL réussie!")
        conn.close()
        
        # Démarrage du serveur
        server = HTTPServer(('localhost', 8000), MonHandler)
        print("Serveur démarré sur http://localhost:8000")
        print("Appuyez sur Ctrl+C pour arrêter le serveur")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        if server:
            server.server_close()
        print("Serveur arrêté")
        
    except mysql.connector.Error as err:
        print(f"Erreur de connexion MySQL: {err}")