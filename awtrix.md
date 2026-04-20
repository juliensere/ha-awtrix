# AWTRIX3 — notes d'API

Device courant : `http://192.168.0.100/`

## Endpoints utiles

- `GET  /api/loop` — liste les apps actuellement dans la rotation (natives + customs) avec leur position.
- `GET  /api/apps` — liste ordonnée des apps natives connues du firmware.
- `GET  /api/settings` — dump complet des réglages.
- `POST /api/settings` — modifie des réglages (JSON partiel).
- `POST /api/custom?name=<app>` — crée/maj une custom app (JSON body). Body vide = suppression.
- `POST /api/notify` — notification ponctuelle (mêmes champs qu'une custom app + `hold`).
- `POST /api/notify/dismiss` — retire une notification `hold:true`.
- `POST /api/reboot` — reboot soft du device.
- `POST /api/switch` avec `{"name":"..."}` — bascule sur une app précise.

## Désactiver les apps natives (Time, Date, Temperature, Humidity, Battery)

Clés booléennes dans `/api/settings` : `TIM`, `DAT`, `TEMP`, `HUM`, `BAT`.

**Piège majeur : "requires reboot".** Modifier ces flags sans rebooter ne change rien au comportement — les apps restent dans `/api/loop`. Il faut impérativement enchaîner avec `POST /api/reboot`.

```bash
curl -X POST http://192.168.0.100/api/settings \
  -H "Content-Type: application/json" \
  -d '{"TIM":false,"DAT":false,"TEMP":false,"HUM":false,"BAT":false}'
curl -X POST http://192.168.0.100/api/reboot
```

Après reboot (~10–15 s), `/api/loop` ne contient plus les natives désactivées.

## Custom apps persistantes

Par défaut une custom app est volatile et disparaît au reboot. Utiliser `"save":true` dans le body pour la stocker en flash et la recharger au boot.

```bash
curl -X POST "http://192.168.0.100/api/custom?name=claude_usage" \
  -H "Content-Type: application/json" \
  -d '{"text":"--%","icon":"71678","duration":6,"pushIcon":2,"save":true}'
```

Attention : la doc officielle déconseille `save:true` pour des customs à forte fréquence de mise à jour (usure flash ESP).

### Champs utiles

- `text` — string, ou tableau de fragments `[{"t":"...","c":"RRGGBB"},...]` pour couleurs mixtes.
- `icon` — ID numérique (ex : `71678`) ou nom de fichier sans extension, ou base64 JPG 8x8.
- `duration` — secondes d'affichage (défaut 5).
- `pushIcon` — 0 fixe / 1 bouge sans réapparition / 2 bouge et réapparaît à chaque scroll.
- `repeat` — nombre de scrolls avant fin (-1 = infini).
- `lifetime` / `lifetimeMode` — auto-suppression si pas de refresh après N secondes (0 = pas d'auto-delete ; mode 1 = marque stale en rouge au lieu de delete).
- `progress` + `progressC` + `progressBC` — barre de progression 0–100.
- `bar` / `line` — graphes (max 16 valeurs, 11 avec icon).

## Pièges rencontrés

- **`POST /api/apps`** ne sert **pas** à cacher les natives. Ça réordonne la liste native connue et peut accidentellement supprimer des customs actifs. À éviter pour notre cas d'usage.
- **Custom app "morte" qui ne réapparaît plus** : après certaines manipulations (notamment un `POST /api/apps` malencontreux), un nom de custom peut rester bloqué — POST `/api/custom?name=X` répond `OK` mais l'app n'est jamais listée dans `/api/loop`. Fix : envoyer un body vide pour delete explicite, puis recréer.
- **`hold:true` sur une notification** fige l'écran sur ce message et masque visuellement la rotation, mais les apps natives restent dans le loop — ce n'est pas une vraie désactivation, et ça ne permet qu'**un seul** message à la fois (donc inutilisable pour faire tourner plusieurs customs).
- Les flags `TIM/DAT/...` peuvent apparaître à `false` dans le dump `/api/settings` alors que les apps natives tournent toujours — parce qu'un reboot n'a jamais été déclenché depuis la modif. Le dump reflète la config stockée, pas l'état runtime.

## État actuel du device (2026-04-14)

- Natives désactivées (`TIM/DAT/TEMP/HUM/BAT = false` + reboot appliqué).
- Deux customs persistantes dans le loop :
  - `claude_usage` — icon `71678`, placeholder `"--%"`.
  - `claude_reset` — icon `71440`, placeholder `"--h--"`.
- Valeurs réelles à brancher ultérieurement (source HA / cron / automation à décider).
