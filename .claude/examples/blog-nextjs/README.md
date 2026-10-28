# Exemple : Blog Next.js

> Projet exemple pour illustrer le workflow D-EPCT+R en mode FULL (v2.6)

## Contexte

Un blog personnel avec Next.js, MDX pour le contenu, et un système de tags.
- **Complexité** : FULL (3-5 jours)
- **Stack** : Next.js 14 + MDX + Tailwind CSS + Vercel

## Fichiers

```
blog-nextjs/
├── README.md              # Ce fichier
├── 01-BRAINSTORM.md       # Session de brainstorming
├── 02-UX-DESIGN.md        # Personas et User Journeys (NEW v2.6)
├── 03-PRD.md              # Product Requirements Document (FULL)
├── 04-ARCHITECTURE.md     # Architecture technique
├── 05-STORIES.md          # Epics et User Stories
└── 06-IMPLEMENTATION.md   # Notes d'implémentation
```

## Workflow utilisé

```bash
# Discovery complet avec validation à chaque étape
/discovery "Blog personnel avec Next.js et MDX"

# Le workflow propose automatiquement UX Design (score 4/5)
# → Personas + User Journeys générés
```

Mode FULL détecté automatiquement (score 4/5) :
- 3+ features distinctes ✅
- Architecture multi-composants ✅
- 3+ pages UI ✅
- Estimation > 1 jour ✅

## Fonctionnalités v2.6 utilisées

| Feature | Usage dans cet exemple |
|---------|------------------------|
| **UX Designer** | Personas lecteur/auteur, journey de lecture |
| **Dynamic Context** | PRD et Architecture chargés automatiquement |
| **Hook coverage** | Coverage affichée après chaque test |

## Commandes utiles v2.6

```bash
# Review une PR
/pr-review #42

# Générer toute la documentation
/docs all

# Refactorer les composants
/refactor src/components/

# Voir l'état du projet
/status
```

---

## Code généré

### Structure du projet

```
blog-nextjs/
├── app/
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── blog/
│   │   ├── page.tsx       # Blog listing
│   │   └── [slug]/
│   │       └── page.tsx   # Blog post
│   └── tags/
│       └── [tag]/
│           └── page.tsx   # Posts by tag
├── components/
│   ├── Header.tsx
│   ├── PostCard.tsx
│   ├── TagList.tsx
│   └── MDXContent.tsx
├── lib/
│   ├── posts.ts           # Post utilities
│   └── mdx.ts             # MDX processing
├── content/
│   └── posts/             # MDX files
└── styles/
    └── globals.css
```

### app/layout.tsx

```typescript
import { Inter } from 'next/font/google';
import Header from '@/components/Header';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Mon Blog',
  description: 'Blog personnel avec Next.js et MDX',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <Header />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
```

### lib/posts.ts

```typescript
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

const postsDirectory = path.join(process.cwd(), 'content/posts');

export interface Post {
  slug: string;
  title: string;
  date: string;
  tags: string[];
  excerpt: string;
  content: string;
}

export async function getAllPosts(): Promise<Post[]> {
  const fileNames = fs.readdirSync(postsDirectory);

  const posts = fileNames
    .filter((fileName) => fileName.endsWith('.mdx'))
    .map((fileName) => {
      const slug = fileName.replace(/\.mdx$/, '');
      const fullPath = path.join(postsDirectory, fileName);
      const fileContents = fs.readFileSync(fullPath, 'utf8');
      const { data, content } = matter(fileContents);

      return {
        slug,
        title: data.title,
        date: data.date,
        tags: data.tags || [],
        excerpt: data.excerpt || '',
        content,
      };
    })
    .sort((a, b) => (a.date < b.date ? 1 : -1));

  return posts;
}

export async function getPostBySlug(slug: string): Promise<Post | null> {
  const fullPath = path.join(postsDirectory, `${slug}.mdx`);

  if (!fs.existsSync(fullPath)) {
    return null;
  }

  const fileContents = fs.readFileSync(fullPath, 'utf8');
  const { data, content } = matter(fileContents);

  return {
    slug,
    title: data.title,
    date: data.date,
    tags: data.tags || [],
    excerpt: data.excerpt || '',
    content,
  };
}

export async function getAllTags(): Promise<string[]> {
  const posts = await getAllPosts();
  const tags = new Set<string>();

  posts.forEach((post) => {
    post.tags.forEach((tag) => tags.add(tag));
  });

  return Array.from(tags).sort();
}
```

### components/PostCard.tsx

```typescript
import Link from 'next/link';
import { Post } from '@/lib/posts';
import TagList from './TagList';

interface PostCardProps {
  post: Post;
}

export default function PostCard({ post }: PostCardProps) {
  return (
    <article className="border rounded-lg p-6 hover:shadow-md transition-shadow">
      <Link href={`/blog/${post.slug}`}>
        <h2 className="text-xl font-bold mb-2 hover:text-blue-600">
          {post.title}
        </h2>
      </Link>

      <time className="text-gray-500 text-sm">
        {new Date(post.date).toLocaleDateString('fr-FR')}
      </time>

      <p className="mt-2 text-gray-700">{post.excerpt}</p>

      <div className="mt-4">
        <TagList tags={post.tags} />
      </div>
    </article>
  );
}
```

### app/blog/[slug]/page.tsx

```typescript
import { notFound } from 'next/navigation';
import { getPostBySlug, getAllPosts } from '@/lib/posts';
import MDXContent from '@/components/MDXContent';
import TagList from '@/components/TagList';

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}

export default async function BlogPost({ params }: Props) {
  const post = await getPostBySlug(params.slug);

  if (!post) {
    notFound();
  }

  return (
    <article className="max-w-3xl mx-auto">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{post.title}</h1>
        <time className="text-gray-500">
          {new Date(post.date).toLocaleDateString('fr-FR')}
        </time>
        <div className="mt-4">
          <TagList tags={post.tags} />
        </div>
      </header>

      <div className="prose prose-lg">
        <MDXContent source={post.content} />
      </div>
    </article>
  );
}
```

### tests/posts.test.ts

```typescript
import { getAllPosts, getPostBySlug, getAllTags } from '@/lib/posts';

describe('Posts Library', () => {
  describe('getAllPosts', () => {
    it('should_return_posts_sorted_by_date_desc', async () => {
      const posts = await getAllPosts();

      for (let i = 1; i < posts.length; i++) {
        expect(new Date(posts[i - 1].date).getTime())
          .toBeGreaterThanOrEqual(new Date(posts[i].date).getTime());
      }
    });
  });

  describe('getPostBySlug', () => {
    it('should_return_null_when_post_not_found', async () => {
      const post = await getPostBySlug('non-existent-post');
      expect(post).toBeNull();
    });
  });

  describe('getAllTags', () => {
    it('should_return_unique_sorted_tags', async () => {
      const tags = await getAllTags();
      const sortedTags = [...tags].sort();
      expect(tags).toEqual(sortedTags);
    });
  });
});
```
