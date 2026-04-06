"use client";

import { useEffect } from "react";
import { setAccessToken } from "@/lib/api";

export function TokenProvider({ token, children }: { token: string; children: React.ReactNode }) {
  setAccessToken(token);

  useEffect(() => {
    setAccessToken(token);
  }, [token]);

  return <>{children}</>;
}
