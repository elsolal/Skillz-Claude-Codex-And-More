# Debate Templates v3.5

> Templates pour les 5 rounds du système Multi-Mind avec débat itératif.

---

## Round 1 : CRITIQUE

### Prompt pour chaque agent

```markdown
Analyse le document suivant en tant que [AGENT_ROLE].

Document à analyser :
---
[DOCUMENT_CONTENT]
---

Fournis une critique structurée :

1. **Score global** : X/10

2. **Points forts** (3 max) :
   - [Point 1]
   - [Point 2]
   - [Point 3]

3. **Points faibles** (5 max) :
   - [Critique 1] - Sévérité: [Critique/Majeure/Mineure]
   - [Critique 2] - Sévérité: [Critique/Majeure/Mineure]
   - ...

4. **Risques identifiés** :
   - [Risque 1] - Probabilité: [Haute/Moyenne/Basse]
   - [Risque 2] - Probabilité: [Haute/Moyenne/Basse]

5. **Recommandations prioritaires** (3 max) :
   - [Recommandation 1]
   - [Recommandation 2]
   - [Recommandation 3]

Sois spécifique et constructif. Chaque critique doit être accompagnée d'une suggestion d'amélioration.
```

### Output attendu

```markdown
### [EMOJI] [AGENT_NAME] - [AGENT_ROLE]

**Score : X/10**

#### Points forts
1. [Description du point fort]
2. [Description du point fort]
3. [Description du point fort]

#### Points faibles
| # | Critique | Sévérité |
|---|----------|----------|
| 1 | [Description] | [Critique/Majeure/Mineure] |
| 2 | [Description] | [Critique/Majeure/Mineure] |

#### Risques
| Risque | Probabilité | Impact |
|--------|-------------|--------|
| [Description] | [H/M/B] | [H/M/B] |

#### Recommandations
1. [Recommandation prioritaire]
2. [Recommandation secondaire]
3. [Recommandation tertiaire]
```

---

## Round 2 : IDENTIFICATION DES FRICTIONS

### Prompt d'analyse

```markdown
Voici les critiques de tous les agents :

[TOUTES_LES_CRITIQUES]

Analyse ces critiques pour identifier les **frictions** (points de désaccord majeurs).

Pour chaque friction identifiée (2-3 max) :

1. **Sujet** : Quel est le point de désaccord ?
2. **Question centrale** : Quelle question doit être tranchée ?
3. **Camp A** : Quels agents soutiennent la position A ? Quelle est leur position ?
4. **Camp B** : Quels agents soutiennent la position B ? Quelle est leur position ?

Critères pour identifier une friction :
- Au moins 2 agents de chaque côté (ou 1 vs reste si argument fort)
- Impact significatif sur le document/code
- Positions clairement opposées, pas juste des nuances

Ne retiens que les désaccords majeurs qui méritent un débat approfondi.
```

### Output attendu

```markdown
## 🔥 Frictions identifiées

### Friction #1 : [Sujet du désaccord]
**Question centrale** : [Question à trancher]

| Camp A | Camp B |
|--------|--------|
| [Agents emoji + noms] | [Agents emoji + noms] |
| **Position** : [Résumé position A] | **Position** : [Résumé position B] |
| **Arguments** : [Points clés] | **Arguments** : [Points clés] |

---

### Friction #2 : [Sujet du désaccord]
**Question centrale** : [Question à trancher]

| Camp A | Camp B |
|--------|--------|
| [Agents] | [Agents] |
| **Position** : [Résumé] | **Position** : [Résumé] |
| **Arguments** : [Points clés] | **Arguments** : [Points clés] |

---

### Friction #3 : [Sujet du désaccord]
**Question centrale** : [Question à trancher]

| Camp A | Camp B |
|--------|--------|
| [Agents] | [Agents] |
| **Position** : [Résumé] | **Position** : [Résumé] |
| **Arguments** : [Points clés] | **Arguments** : [Points clés] |
```

---

## Round 3 : DÉBAT CIBLÉ (Itératif)

### Prompt Tour 1 - Arguments initiaux

**Pour le Camp A :**
```markdown
Tu fais partie du Camp A sur la friction suivante :

**Friction** : [SUJET]
**Question** : [QUESTION CENTRALE]
**Ta position** : [POSITION A]
**Ton camp** : [AGENTS DU CAMP A]

Le Camp B ([AGENTS DU CAMP B]) soutient que : [POSITION B]

Développe tes arguments pour défendre ta position :
1. Pourquoi ta position est-elle la meilleure ?
2. Quels sont les avantages concrets ?
3. Quelles sont les preuves/références qui soutiennent ta position ?
4. Anticipe les objections du Camp B et prépare des réponses

Sois persuasif mais factuel. L'objectif est de convaincre, pas d'avoir raison à tout prix.
```

**Pour le Camp B :**
```markdown
Tu fais partie du Camp B sur la friction suivante :

**Friction** : [SUJET]
**Question** : [QUESTION CENTRALE]
**Ta position** : [POSITION B]
**Ton camp** : [AGENTS DU CAMP B]

Le Camp A ([AGENTS DU CAMP A]) soutient que : [POSITION A]

Développe tes arguments pour défendre ta position :
1. Pourquoi ta position est-elle la meilleure ?
2. Quels sont les avantages concrets ?
3. Quelles sont les preuves/références qui soutiennent ta position ?
4. Anticipe les objections du Camp A et prépare des réponses

Sois persuasif mais factuel. L'objectif est de convaincre, pas d'avoir raison à tout prix.
```

### Prompt Tour 2 - Réponses croisées

**Pour le Camp A :**
```markdown
Voici les arguments du Camp B :

---
[ARGUMENTS_CAMP_B]
---

Tu dois maintenant répondre à ces arguments :

1. **Points d'accord** : Y a-t-il des éléments où le Camp B a raison ?
2. **Contre-arguments** : Pourquoi leurs arguments principaux sont-ils insuffisants ?
3. **Nouvelles perspectives** : As-tu de nouveaux éléments à apporter ?
4. **Proposition de compromis** : Y a-t-il une solution qui satisferait les deux camps ?

Reste constructif. Le but est d'arriver à la meilleure solution, pas de "gagner".
```

**Pour le Camp B :** (symétrique)
```markdown
Voici les arguments du Camp A :

---
[ARGUMENTS_CAMP_A]
---

Tu dois maintenant répondre à ces arguments :

1. **Points d'accord** : Y a-t-il des éléments où le Camp A a raison ?
2. **Contre-arguments** : Pourquoi leurs arguments principaux sont-ils insuffisants ?
3. **Nouvelles perspectives** : As-tu de nouveaux éléments à apporter ?
4. **Proposition de compromis** : Y a-t-il une solution qui satisferait les deux camps ?

Reste constructif. Le but est d'arriver à la meilleure solution, pas de "gagner".
```

### Prompt Tour 3 - Position finale

```markdown
Après 2 tours de débat, voici l'état des échanges :

**Tour 1** :
- Camp A : [RÉSUMÉ]
- Camp B : [RÉSUMÉ]

**Tour 2** :
- Camp A répond : [RÉSUMÉ]
- Camp B répond : [RÉSUMÉ]

En tant que [CAMP A/B], donne ta **position finale** :

1. **Maintiens-tu ta position initiale ?** [Oui/Non/Partiellement]
2. **Concessions** : Sur quoi es-tu prêt à céder ?
3. **Points non négociables** : Qu'est-ce qui reste fondamental ?
4. **Proposition finale** : Quelle solution proposes-tu ?

Si un consensus semble possible, décris-le. Sinon, explique pourquoi la divergence persiste.
```

### Output attendu par friction

```markdown
### 🔥 Friction #[N] : [Sujet]

---

#### Tour 1 - Arguments initiaux

**Camp A ([AGENTS])** :
> [Arguments développés - 3-5 points]
>
> Principaux arguments :
> 1. [Argument 1]
> 2. [Argument 2]
> 3. [Argument 3]

**Camp B ([AGENTS])** :
> [Arguments développés - 3-5 points]
>
> Principaux arguments :
> 1. [Argument 1]
> 2. [Argument 2]
> 3. [Argument 3]

---

#### Tour 2 - Réponses croisées

**Camp A répond au Camp B** :
> **Accords** : [Points d'accord]
>
> **Contre-arguments** :
> - Sur [point 1] : [réponse]
> - Sur [point 2] : [réponse]
>
> **Nouvelle perspective** : [Élément nouveau]
>
> **Compromis proposé** : [Solution intermédiaire]

**Camp B répond au Camp A** :
> **Accords** : [Points d'accord]
>
> **Contre-arguments** :
> - Sur [point 1] : [réponse]
> - Sur [point 2] : [réponse]
>
> **Nouvelle perspective** : [Élément nouveau]
>
> **Compromis proposé** : [Solution intermédiaire]

---

#### Tour 3 - Positions finales

**Camp A - Position finale** :
> **Maintien** : [Oui/Non/Partiellement]
> **Concessions** : [Ce qu'ils acceptent de céder]
> **Non négociable** : [Ce qu'ils maintiennent]
> **Proposition** : [Solution finale proposée]

**Camp B - Position finale** :
> **Maintien** : [Oui/Non/Partiellement]
> **Concessions** : [Ce qu'ils acceptent de céder]
> **Non négociable** : [Ce qu'ils maintiennent]
> **Proposition** : [Solution finale proposée]

---

#### 📊 Résultat de la friction

| Critère | Valeur |
|---------|--------|
| **Statut** | [✅ RÉSOLU / ⚖️ DIVERGENCE] |
| **Tours** | [2 ou 3] |
| **Consensus** | [Description si résolu] |
| **Divergence** | [Description si non résolu] |
| **À trancher par** | [Utilisateur / Équipe / Architecte] |
```

---

## Round 4 : CONVERGENCE

### Prompt pour chaque agent

```markdown
Après le débat, donne ton TOP 3 des points les plus importants à traiter.

**Contexte** :
- Résultats des frictions : [RÉSUMÉ DES DÉBATS]
- Points de consensus émergents : [LISTE]

Pour chaque point de ton TOP 3 :
1. **Description** : Qu'est-ce qui doit être changé/amélioré ?
2. **Justification** : Pourquoi ce point est-il prioritaire ?
3. **Effort estimé** : [Faible/Moyen/Élevé]
4. **Impact** : [Critique/Important/Souhaitable]

Tiens compte des résultats des débats. Si une friction a été résolue, intègre la solution dans tes priorités.

Classe tes 3 points par ordre de priorité (1 = plus important).
```

### Output attendu

```markdown
### [EMOJI] [AGENT_NAME] - TOP 3

| Rang | Point | Justification | Effort | Impact |
|------|-------|---------------|--------|--------|
| 1 | [Point] | [Pourquoi] | [F/M/É] | [C/I/S] |
| 2 | [Point] | [Pourquoi] | [F/M/É] | [C/I/S] |
| 3 | [Point] | [Pourquoi] | [F/M/É] | [C/I/S] |
```

### Calcul du score pondéré

```
Score = Σ (Points × Pondération_Agent × Impact_Weight × Rang_Weight)

Impact_Weight :
- Critique = 3
- Important = 2
- Souhaitable = 1

Rang_Weight :
- Rang 1 = 3
- Rang 2 = 2
- Rang 3 = 1

Pondération_Agent : Voir agent-personalities.md
```

### Agrégation globale

```markdown
## 📊 Convergence globale

### TOP 3 par agent

| Agent | #1 | #2 | #3 |
|-------|-----|-----|-----|
| 🏛️ Claude | [Point] | [Point] | [Point] |
| 🤖 GPT | [Point] | [Point] | [Point] |
| 💎 Gemini | [Point] | [Point] | [Point] |
| 🐉 DeepSeek | [Point] | [Point] | [Point] |
| 🔮 GLM | [Point] | [Point] | [Point] |
| 🌙 Kimi | [Point] | [Point] | [Point] |

### Classement pondéré global

| Rang | Point | Score | Agents | Impact | Effort |
|------|-------|-------|--------|--------|--------|
| 1 | [Point] | 12.5 | 🏛️💎🌙🤖 | Critique | Moyen |
| 2 | [Point] | 9.8 | 🏛️🤖🐉 | Important | Faible |
| 3 | [Point] | 7.2 | 💎🔮🌙 | Important | Élevé |
| 4 | [Point] | 5.5 | 🤖🐉 | Souhaitable | Faible |
| 5 | [Point] | 4.1 | 🔮 | Souhaitable | Moyen |
```

---

## Round 5 : CONSENSUS

### Template de synthèse (Claude rapporteur)

```markdown
## 🧠 Synthèse Multi-Mind

### Métadonnées
- **Document** : [Nom du fichier]
- **Mode** : [PRD/Review]
- **Agents actifs** : [N]/6
- **Durée totale** : [X]m [Y]s
- **Frictions** : [N] identifiées, [M] résolues

---

### Scores des agents

| Agent | Score | Focus principal |
|-------|-------|-----------------|
| 🏛️ Claude | X/10 | [Focus] |
| 🤖 GPT | X/10 | [Focus] |
| 💎 Gemini | X/10 | [Focus] |
| 🐉 DeepSeek | X/10 | [Focus] |
| 🔮 GLM | X/10 | [Focus] |
| 🌙 Kimi | X/10 | [Focus] |

**Score moyen** : X.X/10

---

### ✅ Points de consensus ([N] points)

Points sur lesquels la majorité des agents s'accordent :

| # | Point | Agents d'accord | Priorité |
|---|-------|-----------------|----------|
| 1 | [Description] | 🏛️🤖💎🐉🔮🌙 | P0 |
| 2 | [Description] | 🏛️🤖💎🐉 | P1 |
| 3 | [Description] | 🏛️💎🌙 | P1 |

---

### 🔥 Résultats des débats

| # | Friction | Statut | Conclusion |
|---|----------|--------|------------|
| 1 | [Sujet] | ✅ Résolu | [Consensus atteint : description] |
| 2 | [Sujet] | ⚖️ Divergence | [Positions maintenues, à trancher] |
| 3 | [Sujet] | ✅ Résolu | [Consensus atteint : description] |

---

### ⚖️ Divergences irrésolues ([N] points)

Points où les agents ne s'accordent pas après débat :

| Point | Position A | Position B | Recommandation |
|-------|------------|------------|----------------|
| [Point] | [Agents] : [Position résumée] | [Agents] : [Position résumée] | [Ma recommandation avec justification] |

---

### 📋 TOP 5 Actions prioritaires

Actions concrètes à entreprendre, classées par priorité :

| # | Priorité | Action | Effort | Impact | Source |
|---|----------|--------|--------|--------|--------|
| 1 | **P0** | [Action critique] | [F/M/É] | Critique | Consensus |
| 2 | **P1** | [Action importante] | [F/M/É] | Important | Friction #1 résolue |
| 3 | **P1** | [Action importante] | [F/M/É] | Important | Convergence |
| 4 | **P2** | [Action souhaitable] | [F/M/É] | Souhaitable | Convergence |
| 5 | **P2** | [Action souhaitable] | [F/M/É] | Souhaitable | Recommandation |

---

### 💬 Recommandation finale

[Synthèse de 3-5 phrases avec :
- La qualité globale du document/code analysé
- Les améliorations majeures à apporter
- Les risques principaux identifiés
- La recommandation d'action immédiate]

---

### 🚨 Risques résiduels

Points d'attention qui méritent un suivi :

- [ ] [Risque 1 - lié à divergence non résolue]
- [ ] [Risque 2 - identifié par plusieurs agents]
- [ ] [Risque 3 - impact potentiel élevé]
```

---

## Format du rapport final complet

```markdown
# Multi-Mind Debate Report

**Date** : [YYYY-MM-DD HH:MM]
**Mode** : [PRD|Review]
**Fichier** : [path/to/file]
**Agents** : [N]/6
**Durée** : [X]m [Y]s
**Frictions** : [N] identifiées, [M] résolues

---

## Résumé exécutif

[3-5 phrases résumant :
- Ce qui a été analysé
- Les points forts identifiés
- Les principales améliorations suggérées
- Le résultat des débats (frictions résolues/maintenues)
- La recommandation finale]

---

## Round 1 : Critiques individuelles

[Critiques complètes de chaque agent avec scores, points forts/faibles, risques]

---

## Round 2 : Frictions identifiées

[Liste des 2-3 frictions avec les camps formés et les positions initiales]

---

## Round 3 : Débats ciblés

### Friction #1 : [Sujet]
[Tous les tours d'échange détaillés avec arguments, contre-arguments, positions finales]

### Friction #2 : [Sujet]
[Idem]

### Friction #3 : [Sujet]
[Idem]

---

## Round 4 : Convergence

[TOP 3 de chaque agent + classement pondéré global]

---

## Round 5 : Synthèse finale

[Consensus, résultats débats, divergences, actions prioritaires, recommandation]

---

## Annexes

### Configuration des agents
| Agent | Modèle | API | Tokens utilisés |
|-------|--------|-----|-----------------|
| Claude | claude-opus-4.5 | Native | ~X |
| GPT | gpt-5.2 | Codex CLI | ~X |
| Gemini | gemini-3 | Gemini CLI | ~X |
| DeepSeek | deepseek-reasoner | API REST | ~X |
| GLM | glm-4-0520 | API REST | ~X |
| Kimi | kimi-k2-instruct | OpenRouter | ~X |

### Prompts utilisés
[Référence aux prompts de chaque round - optionnel]
```
