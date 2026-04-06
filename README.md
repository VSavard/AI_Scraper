# 🕷️ AI Web Scraper — Powered by Claude

Web scraper Python assisté par IA (Claude d'Anthropic) avec résolution de CAPTCHA intégrée.

---

## Architecture

```
ai_scraper/
├── ai_scraper/
│   ├── main.py            ← Orchestrateur + CLI
│   ├── scraper.py         ← ScraperSession (HTTP) + PageAnalyzer (BeautifulSoup)
│   ├── captcha_solver.py  ← Résolution CAPTCHA via Claude Vision
│   └── ai_processor.py   ← Traitement IA du contenu scrapé
├── tests/
├── pyproject.toml         ← Dépendances Poetry + config Ruff + Pytest
├── .pre-commit-config.yaml
├── setup.sh               ← Bootstrap automatique
└── README.md
```

### Flux de traitement

```
URL + Prompt
    ↓
ScraperSession.get()          ← Requête HTTP avec headers rotatifs + délais anti-bot
    ↓
PageAnalyzer.detect_captcha() ← Détection CAPTCHA (image / widget / texte)
    ↓ [si CAPTCHA]
CaptchaSolver.auto_solve()    ← Claude Vision → réponse CAPTCHA
    ↓
PageAnalyzer.full_snapshot()  ← Extraction : texte, liens, tableaux, métadonnées
    ↓
AIProcessor.process()         ← Claude analyse le snapshot selon votre prompt
    ↓
Résultat JSON structuré
```

---

## Prérequis

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)

---

## Installation

### Option A — Bootstrap automatique (recommandé)

Le script `setup.sh` installe Poetry si absent, crée le `.venv/` local, installe toutes les
dépendances et active les hooks pre-commit en une seule commande.

```bash
bash setup.sh
```

### Option B — Étapes manuelles

**1. Installer Poetry** (si ce n'est pas déjà fait)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**2. Configurer le venv dans le projet**

```bash
poetry config virtualenvs.in-project true
```

> Crée un dossier `.venv/` à la racine — pratique pour VS Code et les outils qui
> cherchent le venv localement.

**3. Installer les dépendances**

```bash
# Prod + dev (pytest, ruff, pre-commit)
poetry install --with dev

# Prod seulement (déploiement)
poetry install
```

**4. Activer les hooks pre-commit**

```bash
poetry run pre-commit install
```

---

## Configuration

Définissez votre clé API Anthropic dans votre environnement :

```bash
# ~/.bashrc ou ~/.zshrc
export ANTHROPIC_API_KEY="sk-ant-..."
```

Vérifiez que la clé est bien chargée :

```bash
echo $ANTHROPIC_API_KEY
```

---

## Utilisation

### Mode CLI

```bash
# Extraction de données
poetry run ai-scraper \
  --url "https://quotes.toscrape.com" \
  --prompt "Extrais toutes les citations avec auteur et tags en JSON"

# Résumé en streaming
poetry run ai-scraper \
  --url "https://news.ycombinator.com" \
  --prompt "Liste les 10 premiers titres avec leur score" \
  --stream

# Avec proxy + sauvegarde JSON
poetry run ai-scraper \
  --url "https://example.com" \
  --prompt "Extrais tous les prix et produits" \
  --proxy "http://user:pass@proxy:8080" \
  --output results.json \
  --verbose
```

### Mode interactif

```bash
poetry run ai-scraper
```

### Utilisation comme librairie Python

```python
from ai_scraper.main import AIScraper

scraper = AIScraper()

result = scraper.scrape(
    url="https://quotes.toscrape.com",
    prompt="Extrais les 5 premières citations avec leur auteur"
)

if result["success"]:
    print(result["result"])
```

---

## Outils de développement

### Linting et formatage (Ruff)

Ruff remplace à la fois **Flake8** et **Black** dans ce projet.

```bash
# Vérifier le code
poetry run ruff check .

# Corriger automatiquement les erreurs
poetry run ruff check . --fix

# Formater le code
poetry run ruff format .

# Vérifier sans modifier (CI)
poetry run ruff format . --check
```

La configuration Ruff dans `pyproject.toml` active les règles suivantes :

| Préfixe | Origine              | Rôle                              |
|---------|----------------------|-----------------------------------|
| `E/W`   | pycodestyle          | Style PEP 8                       |
| `F`     | Pyflakes             | Erreurs logiques (imports inutilisés, etc.) |
| `I`     | isort                | Ordre des imports                 |
| `B`     | flake8-bugbear       | Bugs fréquents                    |
| `C4`    | flake8-comprehensions| Simplification des compréhensions |
| `UP`    | pyupgrade            | Syntaxe Python moderne            |
| `N`     | pep8-naming          | Conventions de nommage            |
| `SIM`   | flake8-simplify      | Simplification du code            |
| `RUF`   | Ruff natif           | Règles spécifiques à Ruff         |

### Tests (Pytest)

```bash
# Lancer les tests avec couverture
poetry run pytest

# Rapport HTML de couverture
poetry run pytest --cov-report=html
open htmlcov/index.html
```

### Pre-commit

Les hooks s'exécutent automatiquement à chaque `git commit`. Pour lancer manuellement :

```bash
# Sur tous les fichiers
pre-commit run --all-files

# Sur un hook spécifique
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

Hooks configurés dans `.pre-commit-config.yaml` :

| Hook                  | Rôle                                              |
|-----------------------|---------------------------------------------------|
| `ruff`                | Lint + corrections automatiques                   |
| `ruff-format`         | Formatage du code                                 |
| `trailing-whitespace` | Supprime les espaces en fin de ligne              |
| `end-of-file-fixer`   | Ajoute le newline final manquant                  |
| `check-yaml`          | Valide la syntaxe YAML                            |
| `check-toml`          | Valide la syntaxe TOML                            |
| `debug-statements`    | Détecte les `breakpoint()` / `pdb` oubliés       |
| `no-commit-to-branch` | Bloque les commits directs sur `main` / `master`  |

### Référence rapide

```bash
poetry run ai-scraper          # lancer le CLI
poetry run pytest              # tests
poetry run ruff check . --fix  # lint + fix
poetry run ruff format .       # format
pre-commit run --all-files     # vérification complète
poetry add <package>           # ajouter une dépendance prod
poetry add --group dev <pkg>   # ajouter une dépendance dev
poetry update                  # mettre à jour les dépendances
poetry env info                # infos sur le venv actif
```

---

## Résolution de CAPTCHA

| Type de CAPTCHA       | Stratégie                              | Taux de succès |
|-----------------------|----------------------------------------|----------------|
| Image CAPTCHA         | Claude Vision (analyse visuelle)       | ~85-95%        |
| Question mathématique | Claude (contexte HTML)                 | ~95%+          |
| reCAPTCHA v2/v3       | 2captcha / capsolver (service tiers)   | ~99% (payant)  |
| hCaptcha              | capsolver (service tiers)              | ~95% (payant)  |

**Services tiers recommandés pour reCAPTCHA :**

- **2captcha.com** : `poetry add 2captcha-python`
- **capsolver.com** : supporte reCAPTCHA + hCaptcha + Cloudflare Turnstile

---

## Anti-détection intégré

- ✅ Rotation automatique des User-Agents
- ✅ Headers HTTP réalistes (Accept-Language, DNT, Sec-Fetch-*)
- ✅ Délais aléatoires entre les requêtes
- ✅ Back-off exponentiel sur erreur
- ✅ Support proxy HTTP/HTTPS

---

## Prompts d'exemple

```
"Extrais tous les prix et noms de produits en JSON"
"Résume le contenu principal en 5 points"
"Liste tous les liens de navigation principaux"
"Trouve les coordonnées de contact (téléphone, email, adresse)"
"Extrais les données du tableau principal"
"Identifie les avis clients et leur note"
"Quels sont les horaires d'ouverture ?"
```
