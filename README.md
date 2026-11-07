# CAMPUS EVENT

Projet final du module Introduction aux Systèmes d'Information (LSI1).

CAMPUS EVENT permet de centraliser les événements de l'université, les étudiants et les inscriptions. Un étudiant consulte les événements et demande à s'inscrire, l'API vérifie la demande, puis l'administration accepte ou refuse l'inscription.

Équipe : Tassadit Ouzia, Oumaima El Khadraoui, Juliette Jean, Nivine Lahouar

## Contenu du dossier

- `app.py` : l'API REST en Flask (avec la base SQLite)
- `index.html` : le frontend (HTML, CSS, JavaScript avec fetch)
- `requirements.txt` : les bibliothèques Python à installer
- `rapport.pdf` : le rapport du projet

## Installation

Il faut avoir Python 3 installé.

Sous Windows :

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Sous Linux, Mac ou WSL :

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Lancer l'application

```
python app.py
```

Le serveur démarre à l'adresse : **http://127.0.0.1:5000**

Ensuite il suffit d'ouvrir `index.html` dans le navigateur (double-clic sur le fichier). Le serveur doit rester lancé pendant ce temps.

Les données sont enregistrées dans une base SQLite, le fichier `campus_event.db`. Il est créé automatiquement au premier lancement, à partir des listes `students`, `events` et `registrations` qui sont au début de `app.py`. Les données restent donc enregistrées quand on redémarre le serveur.

Pour revenir aux données de départ (par exemple avant de refaire les tests Postman), il suffit d'arrêter le serveur, de supprimer le fichier `campus_event.db` et de relancer `python app.py`.

## Endpoints

| Méthode | Endpoint | Rôle | Code succès |
|---|---|---|---|
| GET | `/events` | Liste des événements (avec les places disponibles) | 200 |
| GET | `/events/<id>` | Détail d'un événement | 200 |
| GET | `/students` | Liste des étudiants | 200 |
| POST | `/registrations` | Créer une inscription | 201 |
| GET | `/registrations` | Liste des inscriptions | 200 |
| GET | `/registrations/<id>` | Détail d'une inscription | 200 |
| PATCH | `/registrations/<id>` | Modifier le statut d'une inscription | 200 |

## Règles métier

Quand on crée une inscription, l'API vérifie dans cet ordre :

| Cas | Code |
|---|---|
| `student_id` ou `event_id` manquant | 400 |
| Étudiant inexistant | 404 |
| Événement inexistant | 404 |
| L'étudiant est déjà inscrit à cet événement | 409 |
| L'événement est complet : inscription créée avec le statut `waitlisted` (liste d'attente) | 201 |
| Tout est bon : inscription créée avec le statut `pending` | 201 |

Seules les inscriptions `pending` et `accepted` prennent une place.

Pour le PATCH, le statut doit être `pending`, `accepted`, `rejected` ou `waitlisted`, sinon l'API renvoie 400. Une inscription qui n'existe pas renvoie 404. On ne peut pas accepter une inscription de la liste d'attente si l'événement est toujours complet (409).

Quand une inscription qui avait une place est refusée, la place se libère : la première personne de la liste d'attente passe automatiquement en `pending`.

## Exemples de requêtes

Voir tous les événements :

```
GET http://127.0.0.1:5000/events
```

Réponse :

```json
{
  "events": [
    {
      "id": 1,
      "title": "Atelier Python",
      "date": "2026-11-20",
      "location": "Salle B12",
      "capacity": 30,
      "available_places": 29
    }
  ]
}
```

Créer une inscription :

```
POST http://127.0.0.1:5000/registrations
Content-Type: application/json

{
  "student_id": 2,
  "event_id": 1
}
```

Réponse (201) :

```json
{
  "message": "Registration created successfully",
  "registration": { "id": 4, "student_id": 2, "event_id": 1, "status": "pending" }
}
```

Accepter une inscription :

```
PATCH http://127.0.0.1:5000/registrations/4
Content-Type: application/json

{
  "status": "accepted"
}
```

Exemple d'erreur, double inscription (409) :

```json
{ "error": "Student already registered to this event" }
```

Événement complet, l'inscription part en liste d'attente (201) :

```json
{
  "message": "Event is full, registration added to the waitlist",
  "registration": { "id": 5, "student_id": 2, "event_id": 3, "status": "waitlisted" }
}
```

Pour tester le cas « événement complet », on peut utiliser l'événement 3 : il a une capacité de 1 et il est déjà pris par l'étudiant 1.

Le dossier `postman/` contient la collection `Campus_Event.postman_collection.json` avec les 10 tests, à importer dans Postman et à lancer dans l'ordre.

## Fonctionnalités bonus

- Base de données SQLite à la place des listes Python
- Liste d'attente (statut `waitlisted`) quand un événement est complet, avec passage automatique en `pending` quand une place se libère
- Formulaire d'inscription qui envoie un `POST /registrations` avec fetch
- Affichage du message de confirmation et d'un ticket après l'inscription
- Messages clairs pour les erreurs 400, 404 et 409
- Message d'erreur si le serveur Flask ne répond pas
- Places disponibles et taux de remplissage pour chaque événement
- Statistiques : nombre d'événements, nombre d'inscriptions, taux de remplissage global
- Compte à rebours jusqu'au prochain événement
- Vue administration pour accepter ou refuser les demandes et gérer la liste d'attente (`PATCH /registrations/<id>`)
- Mise en forme avec CSS, adaptée au téléphone
