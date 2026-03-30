import "next-auth";

declare module "next-auth" {
  interface User {
    role: string;
    tenant_id: string;
    access_token: string;
  }
  interface Session {
    user: User & { id: string; role: string; tenant_id: string };
    access_token: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    role: string;
    tenant_id: string;
    access_token: string;
  }
}
