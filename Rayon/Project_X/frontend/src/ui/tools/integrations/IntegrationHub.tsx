import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useIntegrationsStore } from "../../../stores/integrations";
import {
  INTEGRATION_REGISTRY,
  INTEGRATION_TABS,
  INTEGRATION_TAB_CATEGORIES,
} from "./registry";
import type { IntegrationDef, IntegrationTabId } from "./registry";
import { IntegrationHubCard } from "./IntegrationHubCard";
import { IntegrationModal } from "./IntegrationModal";
import { LoadingSpinner } from "../../common/LoadingSpinner";
import styles from "./IntegrationHub.module.css";

export function IntegrationHub() {
  const integrations = useIntegrationsStore((s) => s.integrations);
  const gatewayProviders = useIntegrationsStore((s) => s.gatewayProviders);
  const llmProviders = useIntegrationsStore((s) => s.llmProviders);
  const loading = useIntegrationsStore((s) => s.loading);
  const [activeTab, setActiveTab] = useState<IntegrationTabId>("llm");
  const [search, setSearch] = useState("");
  const [modalDef, setModalDef] = useState<IntegrationDef | null>(null);

  const visibleCategories = INTEGRATION_TAB_CATEGORIES[activeTab];

  const filtered = useMemo(() => {
    const tabItems = INTEGRATION_REGISTRY.filter((d) =>
      visibleCategories.includes(d.category),
    );
    if (!search.trim()) return tabItems;
    const q = search.toLowerCase();
    return tabItems.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.category.toLowerCase().includes(q),
    );
  }, [search, visibleCategories]);

  const handleTabChange = (id: IntegrationTabId) => {
    setActiveTab(id);
    setSearch("");
  };

  if (loading) {
    return <LoadingSpinner text="Loading integrations..." />;
  }

  const showCategoryLabels = visibleCategories.length > 1;

  return (
    <div className={styles.container}>
      {/* Pill-style sub-tabs */}
      <div className={styles.subTabs}>
        {INTEGRATION_TABS.map((tab) => (
          <button
            key={tab.id}
            className={`${styles.pill} ${activeTab === tab.id ? styles.pillActive : ""}`}
            onClick={() => handleTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search with icon */}
      <div className={styles.searchBar}>
        <Search size={14} className={styles.searchIcon} />
        <input
          className={styles.searchInput}
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Integration cards */}
      <div className={styles.list}>
        {visibleCategories.map((cat) => {
          const items = filtered.filter((d) => d.category === cat);
          if (items.length === 0) return null;
          return (
            <div key={cat} className={styles.category}>
              {showCategoryLabels && (
                <div className={styles.categoryLabel}>{cat}</div>
              )}
              {items.map((def) => {
                const cfg = integrations[def.id];
                const hasCredentials =
                  cfg &&
                  Object.values(cfg.credentials).some((v) => v.length > 0);
                const isConnected = !!(cfg?.enabled && hasCredentials);
                const llmCfg = llmProviders[def.id];
                const isActive =
                  gatewayProviders.has(def.id) ||
                  !!(llmCfg?.enabled && llmCfg.apiKey?.trim());
                return (
                  <IntegrationHubCard
                    key={def.id}
                    def={def}
                    connected={isConnected}
                    gatewayActive={gatewayProviders.has(def.id)}
                    isActive={isActive}
                    onAction={() => setModalDef(def)}
                  />
                );
              })}
            </div>
          );
        })}
      </div>

      <IntegrationModal
        def={modalDef}
        open={!!modalDef}
        onClose={() => setModalDef(null)}
      />
    </div>
  );
}
