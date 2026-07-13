"use client";

import Script from "next/script";
import { useRouter } from "next/navigation";
import { useCallback, useRef } from "react";

import { authApi } from "@/lib/api";
import { setToken } from "@/lib/auth";

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

/**
 * Renders the Google Sign-In button via GIS. On success we exchange the ID
 * token for our JWT at /auth/google. Renders nothing if the client id isn't
 * configured, so the rest of auth still works without Google set up.
 */
export function GoogleSignInButton({ onError }: { onError?: (msg: string) => void }) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);

  const init = useCallback(() => {
    if (!CLIENT_ID || !window.google || !containerRef.current) return;
    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: async (response) => {
        try {
          const { access_token } = await authApi.google(response.credential);
          setToken(access_token);
          router.push("/dashboard");
        } catch {
          onError?.("Google sign-in failed");
        }
      },
    });
    window.google.accounts.id.renderButton(containerRef.current, {
      type: "standard",
      theme: "outline",
      size: "large",
      text: "continue_with",
      width: 320,
    });
  }, [router, onError]);

  if (!CLIENT_ID) return null;

  return (
    <>
      <Script src="https://accounts.google.com/gsi/client" onLoad={init} />
      <div ref={containerRef} className="flex justify-center" />
    </>
  );
}
