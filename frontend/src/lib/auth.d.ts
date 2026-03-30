// NextAuth v5 type augmentation
// Reference: https://authjs.dev/getting-started/typescript#module-augmentation

declare module "@auth/core/types" {
  interface User {
    role: string;
    tenant_id: string;
    access_token: string;
  }
}

declare module "@auth/core/adapters" {
  interface AdapterUser {
    role: string;
    tenant_id: string;
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
