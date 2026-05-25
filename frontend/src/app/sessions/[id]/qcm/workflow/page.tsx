"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import api from "@/lib/api";
import type { WorkflowGraph, WorkflowNode, WorkflowEdge } from "@/types";

// ── Node colours per type ─────────────────────────────────────────────────────
const AGENT_COLORS: Record<string, { bg: string; border: string; icon: string }> = {
  start      : { bg: "#0f172a", border: "#6366f1", icon: "▶" },
  retrieval  : { bg: "#1e293b", border: "#0ea5e9", icon: "🔍" },
  generation : { bg: "#1e293b", border: "#8b5cf6", icon: "✨" },
  correction : { bg: "#1e293b", border: "#f59e0b", icon: "✓" },
  evaluation : { bg: "#1e293b", border: "#22c55e", icon: "📊" },
  end        : { bg: "#0f172a", border: "#64748b", icon: "⏹" },
};

// ── Layout positions for our 6 nodes ─────────────────────────────────────────
const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  START          : { x: 340, y: 30  },
  rag            : { x: 340, y: 140 },
  qcm_generator  : { x: 340, y: 260 },
  qcm_corrector  : { x: 170, y: 400 },
  grade_evaluator: { x: 170, y: 530 },
  END            : { x: 340, y: 670 },
};

const NODE_W = 200;
const NODE_H = 70;

export default function WorkflowVisualizerPage() {
  const params    = useParams();
  const router    = useRouter();
  const sessionId = params.id as string;

  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [graph, setGraph]         = useState<WorkflowGraph | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected]   = useState<WorkflowNode | null>(null);
  const [showState, setShowState] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && sessionId) {
      api.qcm.getWorkflowGraph(sessionId)
        .then(setGraph)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [isAuthenticated, sessionId]);

  if (authLoading || isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Chargement du pipeline…</p>
      </div>
    );
  }

  if (!graph) return (
    <div style={styles.loadingContainer}>
      <p style={styles.loadingText}>Impossible de charger le pipeline.</p>
    </div>
  );

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <Link href={`/sessions/${sessionId}/qcm`} style={styles.backLink}>
          ← Retour aux QCM
        </Link>
        <div style={styles.headerRow}>
          <div>
            <h1 style={styles.title}>
              <span style={styles.titleAccent}>⟳</span> {graph.workflow_name}
            </h1>
            <p style={styles.subtitle}>{graph.description}</p>
          </div>
          <button
            onClick={() => setShowState(!showState)}
            style={showState ? styles.btnActive : styles.btnSecondary}
          >
            {showState ? "▲ Masquer le schéma" : "▼ État partagé"}
          </button>
        </div>
      </div>

      {/* State schema panel */}
      {showState && (
        <div style={styles.statePanel}>
          <p style={styles.statePanelTitle}>📦 QCMState — champs partagés entre agents</p>
          <div style={styles.stateGrid}>
            {Object.entries(graph.state_schema).map(([key, type]) => (
              <div key={key} style={styles.stateRow}>
                <code style={styles.stateKey}>{key}</code>
                <code style={styles.stateType}>{type}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main layout: Graph + Detail panel */}
      <div style={styles.mainLayout}>
        {/* SVG Graph */}
        <div style={styles.graphContainer}>
          <SVGGraph
            nodes={graph.nodes}
            edges={graph.edges}
            selected={selected}
            onSelect={setSelected}
          />
        </div>

        {/* Detail panel */}
        <div style={styles.detailPanel}>
          {selected ? (
            <NodeDetail node={selected} />
          ) : (
            <div style={styles.detailEmpty}>
              <div style={styles.detailEmptyIcon}>🖱️</div>
              <p style={styles.detailEmptyText}>
                Cliquez sur un nœud pour voir ses détails
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div style={styles.legend}>
        {[
          { color: "#6366f1", label: "Entrée / Sortie" },
          { color: "#0ea5e9", label: "RAG Retrieval" },
          { color: "#8b5cf6", label: "Génération" },
          { color: "#f59e0b", label: "Correction" },
          { color: "#22c55e", label: "Évaluation" },
        ].map(({ color, label }) => (
          <div key={label} style={styles.legendItem}>
            <div style={{ ...styles.legendDot, background: color }} />
            <span style={styles.legendLabel}>{label}</span>
          </div>
        ))}
        <div style={styles.legendItem}>
          <svg width={32} height={12}>
            <line x1={0} y1={6} x2={28} y2={6} stroke="#6366f1" strokeWidth={2} strokeDasharray="4 2" />
          </svg>
          <span style={styles.legendLabel}>Conditionnel</span>
        </div>
      </div>
    </div>
  );
}

// ── SVG Graph ─────────────────────────────────────────────────────────────────

function SVGGraph({
  nodes,
  edges,
  selected,
  onSelect,
}: {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selected: WorkflowNode | null;
  onSelect: (n: WorkflowNode) => void;
}) {
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]));

  // Compute midpoints for edge labels
  const getEdgePoints = (edge: WorkflowEdge) => {
    const src  = NODE_POSITIONS[edge.source];
    const tgt  = NODE_POSITIONS[edge.target];
    if (!src || !tgt) return null;
    const x1 = src.x + NODE_W / 2;
    const y1 = src.y + NODE_H;
    const x2 = tgt.x + NODE_W / 2;
    const y2 = tgt.y;
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;
    return { x1, y1, x2, y2, mx, my };
  };

  return (
    <svg
      viewBox="0 0 680 760"
      style={{ width: "100%", maxWidth: 520, height: "auto" }}
    >
      <defs>
        <marker
          id="arrow-direct"
          markerWidth={10} markerHeight={7}
          refX={9} refY={3.5}
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#475569" />
        </marker>
        <marker
          id="arrow-cond"
          markerWidth={10} markerHeight={7}
          refX={9} refY={3.5}
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
        </marker>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Edges */}
      {edges.map((edge, i) => {
        const pts = getEdgePoints(edge);
        if (!pts) return null;
        const isCond = edge.type === "conditional";
        const color  = isCond ? "#6366f1" : "#475569";
        return (
          <g key={i}>
            <line
              x1={pts.x1} y1={pts.y1}
              x2={pts.x2} y2={pts.y2}
              stroke={color}
              strokeWidth={isCond ? 1.5 : 2}
              strokeDasharray={isCond ? "6 3" : undefined}
              markerEnd={isCond ? "url(#arrow-cond)" : "url(#arrow-direct)"}
              opacity={0.7}
            />
            {edge.label && (
              <text
                x={pts.mx} y={pts.my - 5}
                textAnchor="middle"
                fontSize={10}
                fill={color}
                opacity={0.85}
              >
                {edge.label}
              </text>
            )}
          </g>
        );
      })}

      {/* Nodes */}
      {nodes.map(node => {
        const pos       = NODE_POSITIONS[node.id];
        if (!pos) return null;
        const agentType = node.agent_type || node.type;
        const colors    = AGENT_COLORS[agentType] || AGENT_COLORS["retrieval"];
        const isSelected= selected?.id === node.id;
        const isStart   = node.type === "start";
        const isEnd     = node.type === "end";

        return (
          <g
            key={node.id}
            transform={`translate(${pos.x},${pos.y})`}
            onClick={() => onSelect(node)}
            style={{ cursor: "pointer" }}
            filter={isSelected ? "url(#glow)" : undefined}
          >
            {/* Node rect */}
            <rect
              width={NODE_W}
              height={NODE_H}
              rx={isStart || isEnd ? 35 : 12}
              fill={colors.bg}
              stroke={isSelected ? "#fff" : colors.border}
              strokeWidth={isSelected ? 2.5 : 1.5}
            />
            {/* Icon */}
            <text
              x={22} y={42}
              fontSize={18}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {colors.icon}
            </text>
            {/* Label */}
            <text
              x={NODE_W / 2 + 6}
              y={NODE_H / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize={isStart || isEnd ? 12 : 13}
              fontWeight={600}
              fill={isSelected ? "#fff" : "#e2e8f0"}
              fontFamily="'IBM Plex Mono', monospace"
            >
              {node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ── Node Detail Panel ─────────────────────────────────────────────────────────

function NodeDetail({ node }: { node: WorkflowNode }) {
  const agentType = node.agent_type || node.type;
  const colors    = AGENT_COLORS[agentType] || AGENT_COLORS["retrieval"];

  return (
    <div style={styles.detail}>
      <div style={{ ...styles.detailHeader, borderColor: colors.border + "66" }}>
        <span style={styles.detailIcon}>{colors.icon}</span>
        <div>
          <p style={{ ...styles.detailName, color: colors.border }}>{node.label}</p>
          <p style={styles.detailType}>{node.type}{node.agent_type ? ` · ${node.agent_type}` : ""}</p>
        </div>
      </div>
      <p style={styles.detailDescription}>{node.description}</p>
      {node.inputs.length > 0 && (
        <div style={styles.detailSection}>
          <p style={styles.detailSectionTitle}>📥 Entrées</p>
          {node.inputs.map((inp, i) => (
            <div key={i} style={styles.detailChip}><code style={styles.chipCode}>{inp}</code></div>
          ))}
        </div>
      )}
      {node.outputs.length > 0 && (
        <div style={styles.detailSection}>
          <p style={styles.detailSectionTitle}>📤 Sorties</p>
          {node.outputs.map((out, i) => (
            <div key={i} style={styles.detailChip}><code style={styles.chipCode}>{out}</code></div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "#0a0f1e",
    color: "#e2e8f0",
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
    padding: "32px 24px",
    maxWidth: 1200,
    margin: "0 auto",
  },
  loadingContainer: {
    minHeight: "100vh", background: "#0a0f1e",
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center", gap: 16,
  },
  spinner: {
    width: 40, height: 40,
    border: "3px solid #1e293b", borderTop: "3px solid #6366f1",
    borderRadius: "50%",
  },
  loadingText: { color: "#64748b", fontSize: 14 },
  header: { marginBottom: 28 },
  backLink: {
    color: "#6366f1", textDecoration: "none", fontSize: 14,
    display: "block", marginBottom: 14,
  },
  headerRow: {
    display: "flex", justifyContent: "space-between",
    alignItems: "flex-start", flexWrap: "wrap", gap: 12,
  },
  title: { fontSize: 26, fontWeight: 700, color: "#f1f5f9", marginBottom: 6 },
  titleAccent: { color: "#6366f1", marginRight: 8 },
  subtitle: { color: "#64748b", fontSize: 14, maxWidth: 600 },
  btnSecondary: {
    background: "#1e293b", color: "#94a3b8",
    border: "1px solid #334155", borderRadius: 10,
    padding: "8px 16px", fontSize: 13,
    cursor: "pointer", flexShrink: 0,
  },
  btnActive: {
    background: "#6366f120", color: "#818cf8",
    border: "1px solid #6366f133", borderRadius: 10,
    padding: "8px 16px", fontSize: 13,
    cursor: "pointer", flexShrink: 0,
  },
  statePanel: {
    background: "#1e293b", border: "1px solid #334155",
    borderRadius: 12, padding: 20, marginBottom: 24,
  },
  statePanelTitle: {
    fontSize: 13, fontWeight: 600, color: "#6366f1", marginBottom: 14,
  },
  stateGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: 8,
  },
  stateRow: {
    display: "flex", alignItems: "center",
    justifyContent: "space-between",
    background: "#0f172a", borderRadius: 6,
    padding: "6px 12px",
  },
  stateKey: { color: "#a5b4fc", fontSize: 12 },
  stateType: { color: "#64748b", fontSize: 11 },
  mainLayout: {
    display: "grid",
    gridTemplateColumns: "1fr 340px",
    gap: 24,
    alignItems: "start",
  },
  graphContainer: {
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: 16,
    padding: 24,
    display: "flex",
    justifyContent: "center",
  },
  detailPanel: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 16,
    minHeight: 300,
    overflow: "hidden",
  },
  detailEmpty: {
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    height: 300, gap: 12,
  },
  detailEmptyIcon: { fontSize: 36, opacity: 0.4 },
  detailEmptyText: { fontSize: 13, color: "#475569", textAlign: "center" },
  detail: { padding: 24 },
  detailHeader: {
    display: "flex", alignItems: "center", gap: 14,
    borderBottom: "1px solid",
    paddingBottom: 16, marginBottom: 16,
  },
  detailIcon: { fontSize: 28 },
  detailName: { fontSize: 16, fontWeight: 700, marginBottom: 2 },
  detailType: { fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" },
  detailDescription: { fontSize: 14, color: "#94a3b8", lineHeight: 1.6, marginBottom: 20 },
  detailSection: { marginBottom: 16 },
  detailSectionTitle: { fontSize: 12, fontWeight: 600, color: "#64748b", marginBottom: 8 },
  detailChip: { marginBottom: 6 },
  chipCode: {
    fontSize: 12, color: "#a5b4fc",
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: 4, padding: "2px 8px",
  },
  legend: {
    display: "flex", alignItems: "center",
    gap: 24, flexWrap: "wrap",
    marginTop: 24,
    padding: "12px 16px",
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: 10,
  },
  legendItem: { display: "flex", alignItems: "center", gap: 8 },
  legendDot: { width: 10, height: 10, borderRadius: "50%" },
  legendLabel: { fontSize: 12, color: "#64748b" },
};
