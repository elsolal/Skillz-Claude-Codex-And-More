# Exemple de livrable — le « gold standard »

**Version : v3.1.0**

Ce dossier contient la paire de PDF qu'un audit complet doit produire. Elle a été générée sur un **site entièrement fictif** : Atelier Brindille, fleuriste événementiel à Lyon. L'entreprise, les coordonnées, les chiffres, les avis et les concurrents sont inventés pour la démonstration.

- `REFERENCE_Audit_Note_Strategique.pdf` — le diagnostic : verdict en feu tricolore, scores, failles avec leurs preuves, angles morts, axes structurants, roadmap, glossaire.
- `REFERENCE_Plan_Implementation.pdf` — l'exécution : chantiers en quatre temps, snippets prêts à coller, blocs « Où coller ce code », page « Quoi faire si tu es perdu ».

## À quoi sert cet exemple

1. **Gold standard pour l'Agent 11.** C'est le niveau de qualité, de structure et de pédagogie attendu. Si les PDF produits sortent en dessous — charte non appliquée, partie manquante, feu tricolore absent, ton trop technique — il suffit de demander : « **Régénère au niveau de l'exemple du dossier `exemple_livrable/`.** »
2. **Asset commercial.** Il peut être montré à un prospect pour illustrer ce qu'il recevra, en précisant qu'il s'agit d'un cas fictif.

## Référence de FORME uniquement

Cet exemple sert de repère pour la **structure, le ton, la pédagogie et la densité**. Rien d'autre.

**Ne jamais en réutiliser** les données, les chiffres, les constats, les concurrents ni les formulations : ils appartiennent à une démonstration fictive. Dans un vrai audit, chaque donnée provient d'un objet structuré validé, ou est marquée comme non mesurée.

## Ce qui a changé depuis cet exemple (V2 → V3)

L'exemple date de la V2. Sa **partie « scores » est périmée** et ne doit pas être copiée telle quelle :

| Dans l'exemple V2 | Ce que la V3 impose |
|---|---|
| Un « Score global du site » sur 100 | **Interdit.** Aucune note globale, aucune moyenne des dimensions |
| Neuf dimensions notées sur 10 | **Cinq dimensions** : F Fondations, V Visibilité IA, O Opportunité, E Exécution, M Mesure |
| Score affiché seul | Score **plus couverture et confiance** sous chaque barre |

Tout le reste — couverture, sommaire, feu tricolore, mise en page des failles avec « La preuve. », angles morts, axes structurants, glossaire, chantiers et snippets — reste la référence.

La source de vérité de la mise en page demeure `templates/Charte_PDF_RosoAI_V3.md`, dont le bloc d'adaptation prime en cas de divergence avec cet exemple.
