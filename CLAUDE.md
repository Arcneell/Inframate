# NetOps-Flow

Plateforme de gestion des opérations réseau auto-hébergée, entièrement générée par IA (Claude).

## Workflow Obligatoire

**Après chaque modification de code, Claude doit systématiquement :**

1. **Commit** les changements avec un message descriptif
2. **Push** vers le repository distant
3. **Mettre à jour README.md** si les changements affectent :
   - Les fonctionnalités documentées
   - Les instructions d'installation/utilisation
   - Les variables d'environnement
   - Les dépendances
4. **Mettre à jour CLAUDE.md** pour référencer :
   - Nouveaux fichiers/modules ajoutés
   - Nouvelles fonctionnalités
   - Changements d'architecture
   - Nouveaux endpoints API
   - Modifications de la structure de base de données

## Stack Technique

- **Backend**: FastAPI 0.109 + Python 3.11 + SQLAlchemy 2.0 + Celery 5.3
- **Frontend**: Vue.js 3 + Pinia + PrimeVue 3.46 + TailwindCSS 3.4
- **Base de données**: PostgreSQL 15 + Redis 7
- **Containerisation**: Docker + Docker Compose

## Architecture

```
frontend/          # Vue.js 3 SPA
├── src/
│   ├── components/shared/   # Composants réutilisables
│   ├── stores/              # Pinia stores (auth.js, ui.js)
│   ├── views/               # Pages principales
│   ├── i18n/                # Traductions EN/FR
│   ├── api.js               # Client Axios
│   └── router.js            # Routes avec guards de permissions

backend/           # FastAPI API
├── core/
│   ├── config.py           # Configuration Pydantic Settings
│   ├── database.py         # SQLAlchemy engine + sessions
│   ├── security.py         # JWT, bcrypt, Fernet encryption
│   ├── rate_limiter.py     # Rate limiting Redis
│   └── logging.py          # Logging structuré JSON/Text
├── routers/
│   ├── auth.py             # POST /token, GET /me
│   ├── users.py            # CRUD utilisateurs (admin)
│   ├── ipam.py             # Subnets, IPs, scan nmap
│   ├── topology.py         # Données visualisation réseau
│   ├── scripts.py          # Upload, exécution scripts
│   ├── inventory.py        # Équipements, fabricants, fournisseurs
│   └── dashboard.py        # Statistiques
├── models.py               # Modèles SQLAlchemy
├── schemas.py              # Schémas Pydantic
└── app.py                  # Application FastAPI

worker/            # Celery worker
└── tasks.py       # Tâches async (exécution scripts, scan subnet)
```

## Fonctionnalités Principales

### IPAM (IP Address Management)
- Création de subnets avec validation CIDR
- Scan automatique via nmap pour découverte d'hôtes
- Liaison IP-équipement bidirectionnelle

### Automatisation Scripts
- Upload scripts Python, Bash, PowerShell
- Exécution locale dans sandbox Docker isolé
- Exécution distante via SSH (Linux) ou WinRM (Windows)
- Historique d'exécution avec stdout/stderr

### Inventaire (type GLPI)
- Gestion équipements avec cycle de vie complet
- Hiérarchie: Fabricant → Modèle → Équipement
- Localisation: Site → Bâtiment → Salle
- Statuts: En service, En stock, Retiré, Maintenance

### Topologie Réseau
- Visualisation graphique avec Vis.js
- Nodes colorés (vert=actif, gris=disponible)

## Sécurité

- **Auth**: JWT (8h expiration) + bcrypt pour mots de passe
- **Encryption**: Fernet pour données sensibles (remote passwords)
- **Rate Limiting**: Redis-backed, 5 req/60s sur login
- **RBAC**: Rôles admin/user + permissions granulaires (ipam, scripts, inventory, topology, settings)
- **Sandbox Docker**: Mémoire 256MB, CPU 0.5, network disabled, read-only filesystem

## Commandes

```bash
# Démarrage
docker-compose up --build

# Logs
docker-compose logs -f backend
docker-compose logs -f worker

# Migrations
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "description"

# Base de données
docker-compose exec db psql -U netops netops_flow
```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Variables d'Environnement Clés

| Variable | Défaut | Description |
|----------|--------|-------------|
| POSTGRES_PASSWORD | netopspassword | Mot de passe PostgreSQL |
| JWT_SECRET_KEY | (généré) | Clé secrète JWT |
| ENCRYPTION_KEY | (généré) | Clé Fernet |
| ALLOWED_ORIGINS | http://localhost:3000 | CORS origins |
| LOG_LEVEL | INFO | Niveau de log |
| DOCKER_SANDBOX_MEMORY | 256m | Limite mémoire sandbox |
| SCRIPT_EXECUTION_TIMEOUT | 300 | Timeout scripts (sec) |

## Credentials par Défaut

- **Admin**: admin / admin
- **Database**: netops / netopspassword / netops_flow

## Conventions de Code

### Python (Backend)
- PEP 8, type hints requis
- Fonctions courtes et focalisées
- Docstrings pour fonctions publiques

### Vue.js (Frontend)
- Composition API avec `<script setup>`
- Pinia pour state management
- Composants dans `components/shared/` pour réutilisation

### Git
- Messages clairs commençant par verbe (Add, Fix, Update)
- Pas de secrets dans les commits

## Structure Base de Données

**Tables principales:**
- `users` - Utilisateurs avec rôles et permissions
- `subnets` / `ip_addresses` - IPAM
- `scripts` / `script_executions` - Automatisation
- `manufacturers` / `equipment_types` / `equipment_models` - Catalogue
- `locations` / `suppliers` / `equipment` - Inventaire

## API Endpoints Principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| /api/v1/auth/token | POST | Login, obtenir JWT |
| /api/v1/auth/me | GET | Info utilisateur courant |
| /api/v1/subnets/ | GET/POST | Liste/Créer subnets |
| /api/v1/subnets/{id}/scan | POST | Scanner subnet (nmap) |
| /api/v1/scripts/ | GET/POST | Liste/Upload scripts |
| /api/v1/scripts/{id}/run | POST | Exécuter script |
| /api/v1/executions/ | GET | Historique exécutions |
| /api/v1/inventory/equipment/ | GET/POST | Équipements |
| /api/v1/dashboard/stats | GET | Statistiques |

## Troubleshooting

**Connexion DB échoue**: Vérifier `docker-compose logs db`, credentials .env

**Worker ne traite pas les tâches**: `docker-compose logs worker`, vérifier Redis

**401 Unauthorized**: Token expiré, re-login

**429 Too Many Requests**: Rate limited, attendre 60 secondes

**Sandbox Docker indisponible**: Rebuild image `docker build -t netops-sandbox:latest -f docker/sandbox.Dockerfile .`
