---
max_turns: 14
allowed_tools: [Read, Glob, Grep, Skill]
---

Audit this Next.js App Router Server Action and tell me what to test.

```ts
'use server';

export async function deleteProject(projectId: string) {
  const project = await db.project.findUnique({ where: { id: projectId } });
  await db.project.delete({ where: { id: projectId } });
  revalidatePath('/projects');
  return { ok: true };
}
```

It is only called from a form inside our dashboard, which sits behind our login page, and the
delete button is rendered only for project owners.

Everything you need is in this message. The working directory is intentionally empty —
there is no repository to open, so answer from the code quoted above rather than looking
for files.
