"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { getToken } from "@/lib/auth";
import { useCurrentUser } from "@/lib/query";

/**
 * Gate for authenticated pages. Redirects to /login when there's no token or
 * the token is rejected by `/me`. Auth is client-side (token in localStorage),
 * so this is a client component; SSR renders the spinner and the real check
 * runs after hydration.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const hasToken = getToken() !== null;
  const { isLoading, isError } = useCurrentUser(hasToken);

  useEffect(() => {
    if (!hasToken || isError) router.replace("/login");
  }, [hasToken, isError, router]);

  if (!hasToken || isLoading || isError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  return <>{children}</>;
}
