import { base64UrlEncode } from "./base64url";

/** The OAuth redirect URI used for all integrations */
export function getOAuthRedirectUri(): string {
  return `${window.location.protocol}//${window.location.host}/oauth/callback`;
}

/** Generate a PKCE code verifier (48 random bytes → base64url string) */
export function generateCodeVerifier(): string {
  return base64UrlEncode(crypto.getRandomValues(new Uint8Array(48)));
}

/** Generate a PKCE code challenge (SHA-256 of verifier, base64url-encoded) */
export async function generateCodeChallenge(verifier: string): Promise<string> {
  const bytes = new TextEncoder().encode(verifier);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return base64UrlEncode(new Uint8Array(hash));
}

/** Generate a random OAuth state parameter to prevent CSRF */
export function generateOAuthState(): string {
  return base64UrlEncode(crypto.getRandomValues(new Uint8Array(16)));
}

export type OAuthCallbackResult = {
  code: string;
  state: string;
};

/**
 * Open an OAuth authorization URL in a popup, poll until the provider
 * redirects back to /oauth/callback, then resolve with the authorization code.
 */
export function openOAuthPopup(authUrl: string): Promise<OAuthCallbackResult> {
  const popup = window.open(
    authUrl,
    "oauth_popup",
    "width=600,height=700,left=200,top=100,scrollbars=yes",
  );
  if (!popup) {
    return Promise.reject(
      new Error("Popup was blocked. Allow popups for this site and try again."),
    );
  }

  return new Promise<OAuthCallbackResult>((resolve, reject) => {
    const timer = setInterval(() => {
      if (popup.closed) {
        clearInterval(timer);
        reject(new Error("Sign-in was cancelled — popup closed before completing."));
        return;
      }
      try {
        const url = new URL(popup.location.href);
        const isCallback =
          url.pathname.endsWith("/oauth/callback") ||
          url.searchParams.has("code") ||
          url.searchParams.has("error");
        if (isCallback) {
          clearInterval(timer);
          const code = url.searchParams.get("code");
          const state = url.searchParams.get("state") ?? "";
          const error = url.searchParams.get("error");
          const errorDesc = url.searchParams.get("error_description");
          popup.close();
          if (error) {
            reject(new Error(errorDesc ?? `OAuth error: ${error}`));
          } else if (code) {
            resolve({ code, state });
          } else {
            reject(new Error("No authorization code in OAuth callback."));
          }
        }
      } catch {
        // SecurityError: cross-origin access — still on provider domain, keep polling
      }
    }, 300);
  });
}

export type OAuthTokens = {
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
};

/**
 * Exchange an authorization code for tokens by POSTing to the token endpoint.
 * Supports PKCE (code_verifier), optional client_secret, and HTTP Basic auth.
 */
export async function exchangeCodeForTokens(params: {
  tokenUrl: string;
  code: string;
  clientId: string;
  clientSecret?: string;
  codeVerifier?: string;
  redirectUri: string;
  useBasicAuth?: boolean;
}): Promise<OAuthTokens> {
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code: params.code,
    redirect_uri: params.redirectUri,
  });
  if (!params.useBasicAuth) {
    body.set("client_id", params.clientId);
    if (params.clientSecret) {
      body.set("client_secret", params.clientSecret);
    }
  }
  if (params.codeVerifier) {
    body.set("code_verifier", params.codeVerifier);
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/x-www-form-urlencoded",
  };
  if (params.useBasicAuth && params.clientSecret) {
    headers["Authorization"] =
      "Basic " + btoa(`${params.clientId}:${params.clientSecret}`);
  }

  const res = await fetch(params.tokenUrl, {
    method: "POST",
    headers,
    body: body.toString(),
  });

  const data = await res.json().catch(() => ({})) as Record<string, unknown>;
  if (!res.ok) {
    const msg =
      (data.error_description as string | undefined) ??
      (data.error as string | undefined) ??
      `HTTP ${res.status}`;
    throw new Error(`Token exchange failed: ${msg}`);
  }

  return {
    accessToken: String(data.access_token ?? ""),
    refreshToken: data.refresh_token ? String(data.refresh_token) : undefined,
    expiresIn: typeof data.expires_in === "number" ? data.expires_in : undefined,
  };
}
