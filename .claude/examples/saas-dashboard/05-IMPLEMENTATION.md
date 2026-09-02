# Notes d'implémentation - SaaS Dashboard

## Workflow interactif utilisé

```bash
# Discovery complète avec checkpoints
/discovery "Dashboard SaaS pour gestion de projets avec auth, équipes, et billing"

# Sortie approuvée :
# - Brainstorm validé (research-first)
# - PRD créé (mode FULL)
# - Architecture documentée
# - Stories créées + Readiness Check 15/15

# Implémentation par Epic
/dev #epic-1-auth
/dev #epic-2-core
/dev #epic-3-billing
```

## Preuves d'implémentation

Chaque epic conserve son plan validé, ses tests RED→GREEN et son gate dans `docs/quality/`.

## Temps réel vs estimé

| Phase | Estimé | Réel | Notes |
|-------|--------|------|-------|
| Discovery | 4h | 3h | Checkpoints ciblés |
| Epic 1: Auth | 2j | 1.5j | Supabase simple |
| Epic 2: Core | 4j | 5j | Kanban complexe |
| Epic 3: Billing | 2j | 2j | Stripe docs good |
| Polish | 2j | 2j | |
| **Total** | **12j** | **12j** | |

## Défis rencontrés

### 1. RLS Multi-tenant

**Problème** : Policies RLS complexes pour team_members.

**Solution** :
```sql
-- Fonction helper pour vérifier membership
CREATE OR REPLACE FUNCTION is_team_member(team_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = $1
    AND team_members.user_id = auth.uid()
  );
$$ LANGUAGE sql SECURITY DEFINER;

-- Utilisation dans policy
CREATE POLICY "Team members can view tasks"
  ON tasks FOR SELECT
  USING (
    is_team_member(
      (SELECT team_id FROM projects WHERE id = tasks.project_id)
    )
  );
```

### 2. Drag & Drop Performance

**Problème** : Lag sur boards avec 100+ tâches.

**Solution** :
```typescript
// Virtualisation des colonnes
import { useVirtualizer } from '@tanstack/react-virtual';

// Debounce des updates serveur
const debouncedUpdate = useDebouncedCallback(
  (taskId, updates) => updateTask(taskId, updates),
  300
);

// Optimistic updates immédiats
const moveTask = (taskId, newStatus, newPosition) => {
  // 1. Update local immédiat
  kanbanStore.moveTask(taskId, newStatus, newPosition);

  // 2. Sync serveur debounced
  debouncedUpdate(taskId, { status: newStatus, position: newPosition });
};
```

### 3. Stripe Webhooks en dev

**Problème** : Tester webhooks en local.

**Solution** :
```bash
# Stripe CLI forward
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Env var
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### 4. Position des tâches

**Problème** : Réordonner sans recalculer toutes les positions.

**Solution** : Lexorank-like ordering
```typescript
// Positions comme strings: "aaa", "aab", "aac"
function getPositionBetween(before: string, after: string): string {
  // Calcul du milieu lexicographique
  // "aaa" et "aac" → "aab"
}

// Recalcul complet si collision
if (newPosition === existingPosition) {
  await rebalancePositions(projectId, status);
}
```

## Stack finale

| Catégorie | Technologie | Version |
|-----------|-------------|---------|
| Framework | Next.js | 14.1.0 |
| UI | shadcn/ui | latest |
| Styling | Tailwind CSS | 3.4.1 |
| State | Zustand | 4.5.0 |
| Server State | TanStack Query | 5.17.0 |
| Drag & Drop | @dnd-kit | 6.1.0 |
| Backend | Supabase | latest |
| Auth | Supabase Auth | - |
| Billing | Stripe | 14.12.0 |
| Validation | Zod | 3.22.4 |
| Testing | Vitest + Playwright | - |

## Métriques finales

| Métrique | Cible | Réel |
|----------|-------|------|
| Lighthouse Performance | > 90 | 94 |
| Time to Interactive | < 2s | 1.4s |
| API p95 latency | < 200ms | 120ms |
| Drag latency | < 100ms | 60ms |
| Test coverage | > 80% | 85% |
| Bundle size (gzip) | < 200kb | 180kb |

## Checklist finale

- [x] Auth magic link + GitHub fonctionne
- [x] RLS testé (cross-team impossible)
- [x] Kanban fluide avec 200 tâches
- [x] Stripe Checkout + Webhooks OK
- [x] Customer Portal accessible
- [x] Limites Free respectées
- [x] Tests E2E passent (Playwright)
- [x] Review 3 passes OK
- [x] Sentry configuré
- [x] Deployed sur Vercel

## Déploiement

```bash
# Variables d'environnement
NEXT_PUBLIC_SUPABASE_URL=xxx
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=xxx

# Deploy
vercel --prod
```

## Prochaines améliorations (v2)

- [ ] GitHub sync (issues ↔ tasks)
- [ ] Comments sur tasks
- [ ] Notifications (in-app + email)
- [ ] Search full-text
- [ ] Activity feed
- [ ] File attachments (Supabase Storage)
- [ ] Mobile responsive (pas encore optimal)
