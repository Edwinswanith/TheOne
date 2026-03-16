import { useEffect, useMemo, useState } from "react";
import { ChevronRight, ChevronDown, CheckCircle } from "lucide-react";
import type { IntegrationDef } from "./registry";
import { useIntegrationsStore } from "../../../stores/integrations";
import type { IntegrationPermission } from "../../../transport/types";
import {
  normalizeIntegrationCredentials,
  validateIntegrationCredentials,
} from "../../../lib/integration-validation";
import {
  generateCodeVerifier,
  generateCodeChallenge,
  generateOAuthState,
  getOAuthRedirectUri,
  openOAuthPopup,
  exchangeCodeForTokens,
} from "../../../lib/oauth";
import { OAUTH_PROVIDERS } from "../../../lib/oauth-providers";
import { Modal } from "../../common/Modal";
import { Input } from "../../common/Input";
import { PasswordInput } from "../../common/PasswordInput";
import { Select } from "../../common/Select";
import { Button } from "../../common/Button";
import { Toggle } from "../../common/Toggle";
import styles from "./IntegrationModal.module.css";

const PERMISSION_LABELS: Record<
  IntegrationPermission,
  { label: string; description: string }
> = {
  read: {
    label: "Read",
    description: "View and read data from this service",
  },
  write: {
    label: "Create & Send",
    description: "Create new items, send messages, or upload files",
  },
  edit: {
    label: "Edit & Update",
    description: "Modify or update existing items",
  },
};

type IntegrationModalProps = {
  def: IntegrationDef | null;
  open: boolean;
  onClose: () => void;
};

export function IntegrationModal({
  def,
  open,
  onClose,
}: IntegrationModalProps) {
  const integrations = useIntegrationsStore((s) => s.integrations);
  const saveIntegration = useIntegrationsStore((s) => s.saveIntegration);
  const testIntegration = useIntegrationsStore((s) => s.testIntegration);
  const setPermissions = useIntegrationsStore((s) => s.setPermissions);
  const disconnectIntegration = useIntegrationsStore(
    (s) => s.disconnectIntegration,
  );
  const saving = useIntegrationsStore((s) => s.saving);

  const existing = def ? integrations[def.id] : undefined;
  const isConnected =
    existing?.enabled &&
    Object.values(existing?.credentials ?? {}).some((v) => v.length > 0);

  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [guideOpen, setGuideOpen] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    error?: string;
  } | null>(null);
  const [oauthLoading, setOAuthLoading] = useState(false);
  const [oauthError, setOAuthError] = useState<string | null>(null);

  // Model selection state
  const savedModel = existing?.credentials?.model ?? "";
  const initModelSelect = (() => {
    if (!savedModel || def?.models?.includes(savedModel)) return savedModel;
    return "__custom__";
  })();
  const [modelSelect, setModelSelect] = useState(initModelSelect);
  const [modelCustom, setModelCustom] = useState(
    initModelSelect === "__custom__" ? savedModel : "",
  );

  const finalCredentials = useMemo(() => {
    const finalModel = modelSelect === "__custom__" ? modelCustom : modelSelect;
    const next = { ...credentials };
    if (finalModel) {
      next.model = finalModel;
    } else {
      delete next.model;
    }
    return normalizeIntegrationCredentials(def?.id ?? "", next);
  }, [credentials, def?.id, modelCustom, modelSelect]);

  const validationErrors = useMemo(
    () => validateIntegrationCredentials(def?.id ?? "", finalCredentials),
    [def?.id, finalCredentials],
  );

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!open || !def) return;
    const creds = existing?.credentials ?? {};
    setCredentials(creds);
    const m = creds.model ?? "";
    const isPreset = !m || def.models?.includes(m);
    setModelSelect(isPreset ? m : "__custom__");
    setModelCustom(isPreset ? "" : m);
    setGuideOpen(false);
    setTesting(false);
    setTestResult(null);
    setOAuthLoading(false);
    setOAuthError(null);
  }, [open, def, existing?.credentials]);
  /* eslint-enable react-hooks/set-state-in-effect */

  if (!def) return null;
  const defPermissions = def.permissions ?? [];

  const setField = (key: string, value: string) => {
    setCredentials((prev) => ({ ...prev, [key]: value }));
    setTestResult(null);
  };

  const handleTest = async () => {
    if (validationErrors.length > 0) {
      setTestResult({ ok: false, error: validationErrors[0] });
      return;
    }
    setTesting(true);
    setTestResult(null);
    const result = await testIntegration(def.id, finalCredentials);
    setTestResult(result);
    setTesting(false);
  };

  const handleSave = async () => {
    if (validationErrors.length > 0) {
      setTestResult({ ok: false, error: validationErrors[0] });
      return;
    }
    await saveIntegration({
      id: def.id,
      enabled: existing?.enabled ?? true,
      credentials: finalCredentials,
      permissions: existing?.permissions ?? defPermissions,
    });
    onClose();
  };

  const handleDisconnect = async () => {
    await disconnectIntegration(def.id);
    onClose();
  };

  const currentPerms = existing?.permissions ?? defPermissions;

  const togglePermission = (perm: IntegrationPermission, enabled: boolean) => {
    const next = enabled
      ? [...currentPerms, perm]
      : currentPerms.filter((p) => p !== perm);
    setPermissions(def.id, next);
  };

  const isOAuth = def.authType === "oauth" || def.authType === "both";
  const oauthProviderConfig = OAUTH_PROVIDERS[def.id] ?? null;

  const handleOAuthSignIn = async () => {
    if (!oauthProviderConfig) return;
    const clientId = credentials[oauthProviderConfig.clientIdField]?.trim();
    if (!clientId) {
      setOAuthError(`Enter your ${def.fields.find((f) => f.key === oauthProviderConfig.clientIdField)?.label ?? "Client ID"} first.`);
      return;
    }
    setOAuthLoading(true);
    setOAuthError(null);
    try {
      const state = generateOAuthState();
      const redirectUri = getOAuthRedirectUri();
      let codeVerifier: string | undefined;
      let codeChallenge = "";
      if (oauthProviderConfig.usePKCE) {
        codeVerifier = generateCodeVerifier();
        codeChallenge = await generateCodeChallenge(codeVerifier);
      }
      const authUrl = oauthProviderConfig.buildAuthUrl({
        clientId,
        redirectUri,
        state,
        codeChallenge,
        usePKCE: oauthProviderConfig.usePKCE,
        credentials,
      });
      const result = await openOAuthPopup(authUrl);
      if (result.state !== state) {
        throw new Error("OAuth state mismatch — possible CSRF. Please try again.");
      }
      const clientSecret = credentials[oauthProviderConfig.clientSecretField]?.trim();
      const tokens = await exchangeCodeForTokens({
        tokenUrl: oauthProviderConfig.tokenUrl(credentials),
        code: result.code,
        clientId,
        clientSecret: clientSecret || undefined,
        codeVerifier,
        redirectUri,
        useBasicAuth: oauthProviderConfig.useBasicAuth,
      });
      const oauthCredentials: Record<string, string> = {
        ...credentials,
        accessToken: tokens.accessToken,
        ...(tokens.refreshToken ? { refreshToken: tokens.refreshToken } : {}),
        ...(tokens.expiresIn
          ? { tokenExpiry: String(Date.now() + tokens.expiresIn * 1000) }
          : {}),
      };
      await saveIntegration({
        id: def.id,
        enabled: true,
        credentials: oauthCredentials,
        permissions: existing?.permissions ?? defPermissions,
        oauthConnected: true,
      });
      onClose();
    } catch (err) {
      setOAuthError(err instanceof Error ? err.message : String(err));
    } finally {
      setOAuthLoading(false);
    }
  };

  const customModelPlaceholder =
    def.id === "google-ai"
      ? "Enter model name (e.g. gemini-2.5-flash)"
      : "Enter model name (e.g. gpt-4o-2024-11-20)";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Configure ${def.name}`}
      footer={
        <>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving || validationErrors.length > 0}
          >
            {saving ? "Saving..." : "Save"}
          </Button>
        </>
      }
    >
      <div className={styles.form}>
        {/* OAuth sign-in for supported integrations */}
        {isOAuth && existing?.oauthConnected && (
          <div className={styles.oauthConnected}>
            <CheckCircle size={14} />
            <span className={styles.oauthConnectedBadge}>
              Connected via OAuth
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleOAuthSignIn}
              disabled={oauthLoading || !oauthProviderConfig}
            >
              {oauthLoading ? "Connecting…" : "Reconnect"}
            </Button>
          </div>
        )}
        {isOAuth && !existing?.oauthConnected && oauthProviderConfig && (
          <div className={styles.oauthHint}>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleOAuthSignIn}
              disabled={oauthLoading}
            >
              {oauthLoading ? "Connecting…" : `Sign in with ${def.name}`}
            </Button>
          </div>
        )}
        {isOAuth && !oauthProviderConfig && (
          <div className={styles.oauthHint}>
            <Button variant="secondary" size="sm" disabled>
              Sign in with {def.name}
            </Button>
          </div>
        )}
        {oauthError && (
          <div className={styles.oauthError}>{oauthError}</div>
        )}
        {isOAuth && oauthProviderConfig && (
          <div className={styles.oauthRedirectHint}>
            Redirect URI to register in your OAuth app:{" "}
            {getOAuthRedirectUri()}
          </div>
        )}

        {/* Credential fields (always shown as fallback) */}
        {def.fields.map((field) => (
          <div key={field.key} className={styles.field}>
            <label className={styles.label}>{field.label}</label>
            {field.type === "password" ? (
              <PasswordInput
                value={credentials[field.key] ?? ""}
                onChange={(e) => setField(field.key, e.target.value)}
                placeholder={field.placeholder}
              />
            ) : (
              <Input
                value={credentials[field.key] ?? ""}
                onChange={(e) => setField(field.key, e.target.value)}
                placeholder={field.placeholder}
              />
            )}
          </div>
        ))}

        {/* Model selector for LLM providers */}
        {def.models && def.models.length > 0 && (
          <div className={styles.field}>
            <label className={styles.label}>Model</label>
            <Select
              value={modelSelect}
              onChange={(e) => {
                const val = e.target.value;
                setModelSelect(val);
                if (val !== "__custom__") setModelCustom("");
                setTestResult(null);
              }}
            >
              <option value="">Select a model...</option>
              {def.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
              <option value="__custom__">Custom model...</option>
            </Select>
            {modelSelect === "__custom__" && (
              <Input
                value={modelCustom}
                onChange={(e) => {
                  setModelCustom(e.target.value);
                  setTestResult(null);
                }}
                placeholder={customModelPlaceholder}
                style={{ marginTop: "6px" }}
              />
            )}
          </div>
        )}

        {validationErrors.length > 0 && (
          <ul className={styles.validationList}>
            {validationErrors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        )}

        {def.fields.length > 0 && (
          <div className={styles.testRow}>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTest}
              disabled={testing || validationErrors.length > 0}
            >
              {testing ? "Testing..." : "Test Connection"}
            </Button>
            {testResult && (
              <span
                className={`${styles.testResult} ${testResult.ok ? styles.testSuccess : styles.testError}`}
              >
                {testResult.ok
                  ? "Connection successful"
                  : testResult.error ?? "Connection failed"}
              </span>
            )}
          </div>
        )}

        {/* Permissions panel (shown when connected) */}
        {isConnected && defPermissions.length > 0 && (
          <div className={styles.permissionsSection}>
            <div className={styles.permissionsLabel}>Permissions</div>
            {defPermissions.map((perm) => {
              const info = PERMISSION_LABELS[perm];
              const enabled = currentPerms.includes(perm);
              return (
                <div key={perm} className={styles.permissionRow}>
                  <div className={styles.permissionInfo}>
                    <div className={styles.permissionName}>{info.label}</div>
                    <div className={styles.permissionDesc}>
                      {info.description}
                    </div>
                  </div>
                  <Toggle
                    checked={enabled}
                    onChange={(checked) => togglePermission(perm, checked)}
                  />
                </div>
              );
            })}
          </div>
        )}

        <div className={styles.guide}>
          <button
            className={styles.guideToggle}
            onClick={() => setGuideOpen((v) => !v)}
          >
            {guideOpen ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronRight size={14} />
            )}
            Setup Guide
          </button>
          {guideOpen && (
            <ol className={styles.steps}>
              {def.setupSteps.map((step, i) => (
                <li key={i} className={styles.step}>
                  {step}
                </li>
              ))}
            </ol>
          )}
        </div>

        {/* Disconnect button */}
        {isConnected && (
          <div className={styles.disconnectSection}>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDisconnect}
              disabled={saving}
            >
              Disconnect
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
