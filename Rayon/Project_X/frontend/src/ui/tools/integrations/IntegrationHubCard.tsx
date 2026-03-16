import {
  FileText, Table, HardDrive, Calendar, Presentation,
  Users, Mail, Hash, Send, MessageCircle, BookOpen, Search,
  Bot, Brain, Sparkles, Zap, Wind, Layers, Video, Linkedin,
  ChevronRight,
} from "lucide-react";
import type { IntegrationDef } from "./registry";
import styles from "./IntegrationHubCard.module.css";

const ICON_MAP: Record<string, React.ReactNode> = {
  FileText: <FileText size={16} />,
  Table: <Table size={16} />,
  HardDrive: <HardDrive size={16} />,
  Calendar: <Calendar size={16} />,
  Presentation: <Presentation size={16} />,
  Users: <Users size={16} />,
  Mail: <Mail size={16} />,
  Hash: <Hash size={16} />,
  Send: <Send size={16} />,
  MessageCircle: <MessageCircle size={16} />,
  BookOpen: <BookOpen size={16} />,
  Search: <Search size={16} />,
  Bot: <Bot size={16} />,
  Brain: <Brain size={16} />,
  Sparkles: <Sparkles size={16} />,
  Zap: <Zap size={16} />,
  Wind: <Wind size={16} />,
  Layers: <Layers size={16} />,
  Video: <Video size={16} />,
  Linkedin: <Linkedin size={16} />,
};

type IntegrationHubCardProps = {
  def: IntegrationDef;
  connected: boolean;
  gatewayActive?: boolean;
  isActive?: boolean;
  onAction: () => void;
};

export function IntegrationHubCard({
  def,
  connected,
  gatewayActive,
  isActive,
  onAction,
}: IntegrationHubCardProps) {
  return (
    <button
      className={`${styles.card} ${connected ? styles.connected : ""} ${isActive ? styles.active : ""}`}
      onClick={onAction}
    >
      <div className={styles.icon}>
        {ICON_MAP[def.icon] ?? <Search size={16} />}
      </div>
      <div className={styles.body}>
        <div className={styles.nameRow}>
          <span className={styles.name}>{def.name}</span>
          {connected && <span className={styles.dot} />}
          {gatewayActive && <span className={styles.gatewayDot} title="Gateway Active" />}
          {isActive && <span className={styles.activeBadge}>Active</span>}
        </div>
        <div className={styles.desc}>{def.description}</div>
      </div>
      <ChevronRight size={14} className={styles.chevron} />
    </button>
  );
}
