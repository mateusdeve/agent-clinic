/// <reference path="./auth.d.ts" />

import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

// NextAuth v5 beta — jwt callback user param is typed as User | AdapterUser which
// doesn't reflect our augmented User. Use a local interface to carry the extra fields.
interface ExtendedUser {
  id?: string | null;
  email?: string | null;
  name?: string | null;
  role: string;
  tenant_id: string;
  access_token: string;
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  providers: [
    Credentials({
      credentials: {
        email: {},
        password: {},
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const res = await fetch(
            `${process.env.FASTAPI_URL}/auth/login`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                email: credentials.email,
                password: credentials.password,
              }),
            }
          );

          if (!res.ok) {
            return null;
          }

          const data = await res.json();

          return {
            id: data.user_id,
            email: data.email,
            name: data.name,
            role: data.role,
            tenant_id: data.tenant_id,
            access_token: data.access_token,
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        // Cast to ExtendedUser — NextAuth v5 beta doesn't propagate type augmentation
        // into the jwt callback user param type (User | AdapterUser intersection)
        const u = user as unknown as ExtendedUser;
        token.id = u.id as string;
        token.role = u.role;
        token.tenant_id = u.tenant_id;
        token.access_token = u.access_token;
      }
      return token;
    },
    session({ session, token }) {
      // NextAuth v5 beta — session callback session param is typed with AdapterUser
      // which doesn't reflect our augmentations. Use unknown cast pattern.
      const s = session as unknown as {
        user: { id: string; role: string; tenant_id: string };
        access_token: string;
      };
      s.user.id = token.id as string;
      s.user.role = token.role as string;
      s.user.tenant_id = token.tenant_id as string;
      s.access_token = token.access_token as string;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
