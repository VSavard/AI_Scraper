# 🕷️ AI Web Scraper — Powered by Claude

Web scraper Python assisté par IA (Claude d'Anthropic) avec résolution de CAPTCHA intégrée.

## Architecture

```
ai_scraper/
├── main.py            ← Orchestrateur + CLI
├── scraper.py         ← ScraperSession (HTTP) + PageAnalyzer (BeautifulSoup)
├── captcha_solver.py  ← Résolution CAPTCHA via Claude Vision
├── ai_processor.py    ← Traitement IA du contenu scrapé
└── requirements.txt
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

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Utilisation

### Mode CLI

```bash
# Extraction de données
python main.py \
  --url "https://quotes.toscrape.com" \
  --prompt "Extrais toutes les citations avec auteur et tags en JSON"

# Résumé en streaming
python main.py \
  --url "https://news.ycombinator.com" \
  --prompt "Liste les 10 premiers titres avec leur score" \
  --stream

# Avec proxy + sauvegarde
python main.py \
  --url "https://example.com" \
  --prompt "Extrais tous les prix et produits" \
  --proxy "http://user:pass@proxy:8080" \
  --output results.json \
  --verbose
```

### Mode interactif

```bash
python main.py
```

### Utilisation comme librairie Python

```python
from main import AIScraper

scraper = AIScraper()

result = scraper.scrape(
    url="https://quotes.toscrape.com",
    prompt="Extrais les 5 premières citations avec leur auteur"
)

if result["success"]:
    print(result["result"])
```

## Résolution de CAPTCHA

| Type de CAPTCHA       | Stratégie                              | Taux de succès |
|-----------------------|----------------------------------------|----------------|
| Image CAPTCHA         | Claude Vision (analyse visuelle)       | ~85-95%        |
| Question mathématique | Claude (contexte HTML)                 | ~95%+          |
| reCAPTCHA v2/v3       | 2captcha / capsolver (service tiers)   | ~99% (payant)  |
| hCaptcha              | capsolver (service tiers)              | ~95% (payant)  |

### Services tiers recommandés pour reCAPTCHA

- **2captcha.com** : `pip install 2captcha-python`
- **capsolver.com** : supporte reCAPTCHA + hCaptcha + Cloudflare Turnstile

## Anti-détection intégré

- ✅ Rotation automatique des User-Agents
- ✅ Headers HTTP réalistes (Accept-Language, DNT, Sec-Fetch-*)
- ✅ Délais aléatoires entre les requêtes
- ✅ Back-off exponentiel sur erreur
- ✅ Support proxy HTTP/HTTPS

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
