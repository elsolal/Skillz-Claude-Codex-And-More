# Exemple : SaaS Dashboard

> Projet exemple pour illustrer le workflow D-EPCT+R complet (v2.6)

## Contexte

Dashboard SaaS pour une application de gestion de projets avec authentification,
équipes, et analytics.
- **Complexité** : FULL+ (1-2 semaines)
- **Stack** : Next.js 14 + Supabase + Stripe + Tailwind

## Fichiers

```
saas-dashboard/
├── README.md              # Ce fichier
├── 01-BRAINSTORM.md       # Research-first + Creative
├── 02-UX-DESIGN.md        # Personas et User Journeys (NEW v2.6)
├── 03-PRD.md              # PRD Full détaillé
├── 04-UI-DESIGN.md        # Design Tokens et Composants (NEW v2.6)
├── 05-ARCHITECTURE.md     # Architecture complète avec ADRs
├── 06-STORIES.md          # 3 Epics, 15+ Stories
└── 07-IMPLEMENTATION.md   # Notes d'implémentation et preuves
```

## Workflow utilisé

```bash
# Discovery complète avec checkpoints
/discovery "Dashboard SaaS pour gestion de projets"

# Le workflow génère automatiquement :
# - Brainstorm (Research-first)
# - UX Design (Personas: Admin, Manager, Member)
# - PRD Full
# - UI Design (Design tokens, composants)
# - Architecture (ADRs inclus)
# - Stories (15+ avec Readiness Check)

# Implémentation de chaque Epic avec un plan validé
/dev #epic-1
/dev #epic-2
/dev #epic-3
```

## Particularités de cet exemple

1. **Research-first** : Analyse de la concurrence avant brainstorm
2. **UX/UI Design** : Auto-triggered car 5+ écrans et design system nécessaire
3. **Architecture complexe** : Multi-tenant, Row Level Security
4. **Preuves versionnées** : un quality gate par epic
5. **3 Epics** : Auth, Projects, Billing

## Fonctionnalités v2.6 utilisées

| Feature | Usage dans cet exemple |
|---------|------------------------|
| **UX Designer** | 3 personas, 5 user journeys |
| **UI Designer** | Design tokens, 12 composants spécifiés |
| **Mode --verbose** | Logs détaillés pour debugging |
| **Dynamic Context** | Tous les docs chargés automatiquement |
| **Hook GitHub auth** | Vérifie auth avant création d'issues |
| **Hook auto-lint** | Lint automatique à chaque modification |
| **Hook coverage** | Coverage après chaque test run |

## Commandes utiles v2.6

```bash
# Voir l'état complet du projet
/status

# Review une PR avec les 3 passes
/pr-review #123

# Générer toute la documentation
/docs all

# Quick fix pour hotfix urgent
/quick-fix "corriger le bug de refresh token"

# Refactorer un module
/refactor src/features/auth/
```

## Preuves de qualité

Les gates de chaque epic sont sauvegardés dans `docs/quality/` et référencent les commandes de
vérification réellement exécutées.

---

## Code généré

### Structure du projet

```
saas-dashboard/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Landing page
│   ├── (auth)/
│   │   ├── login/page.tsx      # Login page
│   │   └── signup/page.tsx     # Signup page
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Dashboard layout
│   │   ├── page.tsx            # Dashboard home
│   │   ├── projects/
│   │   │   ├── page.tsx        # Projects list
│   │   │   └── [id]/page.tsx   # Project detail
│   │   ├── team/page.tsx       # Team management
│   │   └── settings/
│   │       ├── page.tsx        # Settings
│   │       └── billing/page.tsx # Billing
├── components/
│   ├── ui/                     # Design system components
│   ├── dashboard/              # Dashboard-specific
│   └── providers/              # Context providers
├── lib/
│   ├── supabase/
│   │   ├── client.ts           # Browser client
│   │   ├── server.ts           # Server client
│   │   └── middleware.ts       # Auth middleware
│   ├── stripe/
│   │   └── client.ts           # Stripe client
│   └── utils.ts
├── types/
│   └── database.ts             # Supabase types
└── middleware.ts               # Next.js middleware
```

### lib/supabase/server.ts

```typescript
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import type { Database } from '@/types/database';

export function createClient() {
  const cookieStore = cookies();

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          cookieStore.set({ name, value, ...options });
        },
        remove(name: string, options: CookieOptions) {
          cookieStore.delete({ name, ...options });
        },
      },
    }
  );
}

export async function getUser() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

export async function getUserWithTeam() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) return null;

  const { data: membership } = await supabase
    .from('team_members')
    .select('team:teams(*), role')
    .eq('user_id', user.id)
    .single();

  return { user, team: membership?.team, role: membership?.role };
}
```

### lib/supabase/middleware.ts

```typescript
import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({
    request: { headers: request.headers },
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({ name, value, ...options });
          response.cookies.set({ name, value, ...options });
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({ name, value: '', ...options });
          response.cookies.set({ name, value: '', ...options });
        },
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();

  // Protected routes
  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect logged users away from auth pages
  if (user && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return response;
}
```

### app/(dashboard)/projects/page.tsx

```typescript
import { createClient } from '@/lib/supabase/server';
import { ProjectCard } from '@/components/dashboard/ProjectCard';
import { CreateProjectButton } from '@/components/dashboard/CreateProjectButton';

export default async function ProjectsPage() {
  const supabase = createClient();

  const { data: projects, error } = await supabase
    .from('projects')
    .select(`
      *,
      team:teams(name),
      _count:tasks(count)
    `)
    .order('updated_at', { ascending: false });

  if (error) {
    throw new Error('Failed to load projects');
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Projects</h1>
        <CreateProjectButton />
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No projects yet</p>
          <CreateProjectButton variant="outline" className="mt-4" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### components/dashboard/ProjectCard.tsx

```typescript
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Project } from '@/types/database';

interface ProjectCardProps {
  project: Project & {
    team: { name: string } | null;
    _count: { count: number };
  };
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/dashboard/projects/${project.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{project.name}</CardTitle>
            <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
              {project.status}
            </Badge>
          </div>
          <CardDescription>{project.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{project._count.count} tasks</span>
            <span>
              Updated {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
```

### app/api/webhooks/stripe/route.ts

```typescript
import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/lib/supabase/server';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-06-20',
});

export async function POST(request: Request) {
  const body = await request.text();
  const signature = headers().get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    console.error('Webhook signature verification failed');
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  const supabase = createClient();

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;

      await supabase
        .from('subscriptions')
        .upsert({
          team_id: session.metadata?.team_id,
          stripe_customer_id: session.customer as string,
          stripe_subscription_id: session.subscription as string,
          status: 'active',
          plan: session.metadata?.plan || 'pro',
        });
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;

      await supabase
        .from('subscriptions')
        .update({
          status: subscription.status,
          current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        })
        .eq('stripe_subscription_id', subscription.id);
      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;

      await supabase
        .from('subscriptions')
        .update({ status: 'canceled' })
        .eq('stripe_subscription_id', subscription.id);
      break;
    }
  }

  return NextResponse.json({ received: true });
}
```

### types/database.ts

```typescript
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      teams: {
        Row: {
          id: string;
          name: string;
          slug: string;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['teams']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['teams']['Insert']>;
      };
      team_members: {
        Row: {
          id: string;
          team_id: string;
          user_id: string;
          role: 'owner' | 'admin' | 'member';
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['team_members']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['team_members']['Insert']>;
      };
      projects: {
        Row: {
          id: string;
          team_id: string;
          name: string;
          description: string | null;
          status: 'active' | 'archived';
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['projects']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['projects']['Insert']>;
      };
      subscriptions: {
        Row: {
          id: string;
          team_id: string;
          stripe_customer_id: string;
          stripe_subscription_id: string;
          status: 'active' | 'canceled' | 'past_due';
          plan: 'free' | 'pro' | 'enterprise';
          current_period_end: string | null;
          created_at: string;
        };
        Insert: Omit<Database['public']['Tables']['subscriptions']['Row'], 'id' | 'created_at'>;
        Update: Partial<Database['public']['Tables']['subscriptions']['Insert']>;
      };
    };
  };
}

export type Team = Database['public']['Tables']['teams']['Row'];
export type Project = Database['public']['Tables']['projects']['Row'];
export type Subscription = Database['public']['Tables']['subscriptions']['Row'];
```

### tests/projects.test.ts

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createClient } from '@/lib/supabase/server';

vi.mock('@/lib/supabase/server');

describe('Projects', () => {
  const mockSupabase = {
    from: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    insert: vi.fn().mockReturnThis(),
    update: vi.fn().mockReturnThis(),
    delete: vi.fn().mockReturnThis(),
    eq: vi.fn().mockReturnThis(),
    order: vi.fn().mockReturnThis(),
    single: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(createClient).mockReturnValue(mockSupabase as any);
  });

  describe('getProjects', () => {
    it('should_return_projects_ordered_by_updated_at', async () => {
      const mockProjects = [
        { id: '1', name: 'Project A', updated_at: '2024-01-02' },
        { id: '2', name: 'Project B', updated_at: '2024-01-01' },
      ];

      mockSupabase.order.mockResolvedValue({ data: mockProjects, error: null });

      const supabase = createClient();
      const { data } = await supabase
        .from('projects')
        .select('*')
        .order('updated_at', { ascending: false });

      expect(data).toEqual(mockProjects);
      expect(mockSupabase.from).toHaveBeenCalledWith('projects');
    });
  });

  describe('createProject', () => {
    it('should_create_project_with_team_id', async () => {
      const newProject = { name: 'New Project', team_id: 'team-1' };
      const createdProject = { id: '3', ...newProject };

      mockSupabase.single.mockResolvedValue({ data: createdProject, error: null });

      const supabase = createClient();
      const { data } = await supabase
        .from('projects')
        .insert(newProject)
        .select()
        .single();

      expect(data).toEqual(createdProject);
    });
  });
});
```
