/**
 * Per-provider OAuth 2.0 configuration.
 *
 * Each entry describes how to build the authorization URL, where to exchange
 * the code for tokens, which fields carry the client credentials, and whether
 * PKCE is used.
 *
 * Only integrations that support a browser-side OAuth popup flow are listed
 * here. Integrations absent from this map fall back to manual token entry.
 */

export type OAuthProviderConfig = {
  /** Build the authorization URL given the integration's credentials + PKCE params */
  buildAuthUrl(params: {
    clientId: string;
    redirectUri: string;
    state: string;
    codeChallenge: string;
    usePKCE: boolean;
    credentials: Record<string, string>;
  }): string;
  /** Token exchange endpoint URL */
  tokenUrl(credentials: Record<string, string>): string;
  /** Credential field name that holds the OAuth client ID */
  clientIdField: string;
  /** Credential field name that holds the client secret (empty string if not required) */
  clientSecretField: string;
  /** Whether to generate a PKCE code_verifier / code_challenge pair */
  usePKCE: boolean;
  /** Whether token exchange uses HTTP Basic auth instead of body client_id/secret */
  useBasicAuth?: boolean;
};

// ─── Google Workspace ───────────────────────────────────────────────────────

const GOOGLE_SCOPES: Record<string, string[]> = {
  "google-meet": [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "email",
    "profile",
  ],
  "google-docs": [
    "https://www.googleapis.com/auth/documents",
    "openid",
    "email",
    "profile",
  ],
  "google-sheets": [
    "https://www.googleapis.com/auth/spreadsheets",
    "openid",
    "email",
    "profile",
  ],
  "google-slides": [
    "https://www.googleapis.com/auth/presentations",
    "openid",
    "email",
    "profile",
  ],
  "google-drive": [
    "https://www.googleapis.com/auth/drive",
    "openid",
    "email",
    "profile",
  ],
};

function makeGoogleProvider(integrationId: string): OAuthProviderConfig {
  return {
    buildAuthUrl({ clientId, redirectUri, state, codeChallenge, usePKCE }) {
      const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
      url.searchParams.set("client_id", clientId);
      url.searchParams.set("redirect_uri", redirectUri);
      url.searchParams.set("response_type", "code");
      url.searchParams.set(
        "scope",
        (GOOGLE_SCOPES[integrationId] ?? ["openid", "email", "profile"]).join(" "),
      );
      url.searchParams.set("state", state);
      url.searchParams.set("access_type", "offline");
      url.searchParams.set("prompt", "consent");
      if (usePKCE) {
        url.searchParams.set("code_challenge", codeChallenge);
        url.searchParams.set("code_challenge_method", "S256");
      }
      return url.toString();
    },
    tokenUrl: () => "https://oauth2.googleapis.com/token",
    clientIdField: "clientId",
    clientSecretField: "clientSecret",
    usePKCE: true,
  };
}

// ─── Microsoft ──────────────────────────────────────────────────────────────

const MICROSOFT_SCOPES: Record<string, string[]> = {
  "microsoft-teams": [
    "https://graph.microsoft.com/ChannelMessage.Read.All",
    "https://graph.microsoft.com/ChannelMessage.Send",
    "offline_access",
    "openid",
    "profile",
  ],
  "microsoft-outlook": [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.Send",
    "offline_access",
    "openid",
    "profile",
  ],
  "microsoft-calendar": [
    "https://graph.microsoft.com/Calendars.ReadWrite",
    "offline_access",
    "openid",
    "profile",
  ],
};

function makeMicrosoftProvider(integrationId: string): OAuthProviderConfig {
  return {
    buildAuthUrl({ clientId, redirectUri, state, codeChallenge, usePKCE, credentials }) {
      const tenantId = credentials.tenantId || "common";
      const url = new URL(
        `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize`,
      );
      url.searchParams.set("client_id", clientId);
      url.searchParams.set("redirect_uri", redirectUri);
      url.searchParams.set("response_type", "code");
      url.searchParams.set(
        "scope",
        (MICROSOFT_SCOPES[integrationId] ?? ["openid", "profile", "offline_access"]).join(" "),
      );
      url.searchParams.set("state", state);
      url.searchParams.set("response_mode", "query");
      if (usePKCE) {
        url.searchParams.set("code_challenge", codeChallenge);
        url.searchParams.set("code_challenge_method", "S256");
      }
      return url.toString();
    },
    tokenUrl: (creds) =>
      `https://login.microsoftonline.com/${creds.tenantId || "common"}/oauth2/v2.0/token`,
    clientIdField: "appId",
    clientSecretField: "appSecret",
    usePKCE: true,
  };
}

// ─── LinkedIn ───────────────────────────────────────────────────────────────

const linkedInProvider: OAuthProviderConfig = {
  buildAuthUrl({ clientId, redirectUri, state }) {
    const url = new URL("https://www.linkedin.com/oauth/v2/authorization");
    url.searchParams.set("client_id", clientId);
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("scope", "r_liteprofile r_emailaddress w_member_social");
    url.searchParams.set("state", state);
    return url.toString();
  },
  tokenUrl: () => "https://www.linkedin.com/oauth/v2/accessToken",
  clientIdField: "clientId",
  clientSecretField: "clientSecret",
  usePKCE: false, // LinkedIn does not support PKCE
};

// ─── Notion ─────────────────────────────────────────────────────────────────

const notionProvider: OAuthProviderConfig = {
  buildAuthUrl({ clientId, redirectUri, state }) {
    const url = new URL("https://api.notion.com/v1/oauth/authorize");
    url.searchParams.set("client_id", clientId);
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("response_type", "code");
    url.searchParams.set("owner", "user");
    url.searchParams.set("state", state);
    return url.toString();
  },
  tokenUrl: () => "https://api.notion.com/v1/oauth/token",
  clientIdField: "clientId",
  clientSecretField: "clientSecret",
  usePKCE: false,
  useBasicAuth: true,
};

// ─── Slack ───────────────────────────────────────────────────────────────────

const slackProvider: OAuthProviderConfig = {
  buildAuthUrl({ clientId, redirectUri, state }) {
    const url = new URL("https://slack.com/oauth/v2/authorize");
    url.searchParams.set("client_id", clientId);
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("state", state);
    url.searchParams.set(
      "scope",
      "channels:read,channels:history,chat:write,users:read",
    );
    return url.toString();
  },
  tokenUrl: () => "https://slack.com/api/oauth.v2.access",
  clientIdField: "clientId",
  clientSecretField: "clientSecret",
  usePKCE: false,
};

// ─── Registry ───────────────────────────────────────────────────────────────

export const OAUTH_PROVIDERS: Record<string, OAuthProviderConfig> = {
  "google-meet": makeGoogleProvider("google-meet"),
  "google-docs": makeGoogleProvider("google-docs"),
  "google-sheets": makeGoogleProvider("google-sheets"),
  "google-slides": makeGoogleProvider("google-slides"),
  "google-drive": makeGoogleProvider("google-drive"),
  "microsoft-teams": makeMicrosoftProvider("microsoft-teams"),
  "microsoft-outlook": makeMicrosoftProvider("microsoft-outlook"),
  "microsoft-calendar": makeMicrosoftProvider("microsoft-calendar"),
  linkedin: linkedInProvider,
  notion: notionProvider,
  slack: slackProvider,
};
