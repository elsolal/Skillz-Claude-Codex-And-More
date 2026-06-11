# Modele de preuve

## Statuts

| Statut | Definition | Exemple |
|---|---|---|
| `Confirmé` | Observe directement dans la page, le DOM, une capture, la console, le reseau, ou une source fournie | Le H1 visible sur `/pricing` est "Plans" |
| `Déduit` | Inference raisonnable a partir d'un signal observe, mais non prouvee directement | Le site semble Next.js via `_next/` dans les requetes |
| `Non vérifié` | Hypothese, manque d'acces, page non chargee, login absent, evidence insuffisante | Impossible de confirmer le dashboard sans compte test |

## Champs minimaux

Pour chaque finding important:

- `claim`: information ou probleme formule clairement;
- `status`: `Confirmé`, `Déduit`, `Non vérifié`;
- `evidence`: URL, screenshot, snapshot, commande, request id ou extrait court;
- `limit`: ce qui manque ou peut biaiser l'observation;
- `next_check`: verification suivante si la conclusion compte pour une decision.

## Regles anti-hallucination

- Ne jamais conclure "n'existe pas" apres une seule page visitee.
- Distinguer "non visible dans ce viewport" de "absent du site".
- Quand un site personnalise par localisation, compte, cookie ou AB test, le signal est local a la session.
- Pour les concurrents, refuser l'analyse detaillee sans URL et source accessible.
- Pour les sites publics, citer les pages visitees et non le domaine generique.
