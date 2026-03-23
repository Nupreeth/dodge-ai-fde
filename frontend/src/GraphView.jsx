import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API_BASE = import.meta.env.VITE_API_URL;

const PRIMARY_TYPES = new Set([
  "sales_order_header",
  "billing_document_header",
  "outbound_delivery_header",
]);

const TYPE_LABELS = {
  sales_order_header: "Sales Order",
  billing_document_header: "Billing Doc",
  outbound_delivery_header: "Delivery",
  product: "Product",
  business_partner: "Partner",
  payment: "Payment",
  journal_entry_item: "Journal",
};

const LEGEND_ITEMS = [
  { label: "Sales Order", color: "#93c5fd" },
  { label: "Billing Doc", color: "#93c5fd" },
  { label: "Delivery", color: "#93c5fd" },
  { label: "Product", color: "#f9a8a8" },
  { label: "Partner", color: "#f9a8a8" },
  { label: "Payment", color: "#f9a8a8" },
  { label: "Journal", color: "#f9a8a8" },
];

const GraphView = ({ highlightedIds = [], onGraphData, isMinimized }) => {
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [size, setSize] = useState({ width: 400, height: 400 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loadingNeighbors, setLoadingNeighbors] = useState(false);
  const [hideLabels, setHideLabels] = useState(false);

  const highlightedSet = useMemo(
    () => new Set(highlightedIds || []),
    [highlightedIds]
  );

  useEffect(() => {
    if (!containerRef.current) {
      return undefined;
    }

    const updateSize = () => {
      const rect = containerRef.current.getBoundingClientRect();
      setSize({ width: Math.max(1, rect.width), height: Math.max(1, rect.height) });
    };

    updateSize();

    const observer = new ResizeObserver(() => updateSize());
    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const response = await fetch(`${API_BASE}/graph`);
        const data = await response.json();
        const formatted = {
          nodes: data.nodes || [],
          links: (data.edges || []).map((edge) => ({
            source: edge.source,
            target: edge.target,
          })),
        };
        setGraphData(formatted);
        if (onGraphData) {
          onGraphData(data);
        }
      } catch (error) {
        setGraphData({ nodes: [], links: [] });
      }
    };

    fetchGraph();
  }, [onGraphData]);

  const handleNodeClick = async (node) => {
    if (!node) {
      return;
    }

    setSelectedNode({
      id: node.id,
      type: node.type,
      data: node.data || {},
    });

    setLoadingNeighbors(true);
    try {
      await fetch(`${API_BASE}/expand/${encodeURIComponent(node.id)}`);
    } catch (error) {
      // Ignore neighbor fetch failures for now.
    } finally {
      setLoadingNeighbors(false);
    }
  };

  const nodeColor = (node) => {
    if (highlightedSet.has(node.id)) {
      return "#FFD700";
    }
    return PRIMARY_TYPES.has(node.type) ? "#93c5fd" : "#f9a8a8";
  };

  const nodeVal = (node) => (highlightedSet.has(node.id) ? 10 : 5);

  const nodeLabel = (node) => TYPE_LABELS[node.type] || node.type || "";

  const getConnectionsCount = (nodeId) => {
    return (graphData.links || []).filter((link) => {
      const sourceId = typeof link.source === "object" ? link.source.id : link.source;
      const targetId = typeof link.target === "object" ? link.target.id : link.target;
      return sourceId === nodeId || targetId === nodeId;
    }).length;
  };

  const renderFieldRows = (data) => {
    const entries = Object.entries(data || {});
    const limited = entries.slice(0, 6);

    return (
      <>
        {limited.map(([key, value]) => (
          <div key={key} style={{ marginBottom: 6, fontSize: 13, color: "#2f2f2f" }}>
            <strong style={{ fontWeight: 600 }}>{key}:</strong>{" "}
            <span>{value === null || value === undefined || value === "" ? "-" : String(value)}</span>
          </div>
        ))}
        {entries.length > 6 && (
          <div
            style={{
              marginTop: 8,
              fontSize: 12,
              color: "#8b8b8b",
              fontStyle: "italic",
            }}
          >
            Additional fields hidden for readability
          </div>
        )}
      </>
    );
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        backgroundColor: "#f5f5f5",
      }}
    >
      {!isMinimized && (
        <div style={{ position: "absolute", top: 12, left: 12, display: "flex", gap: 8, zIndex: 2 }}>
          <button
            type="button"
            onClick={() => setHideLabels((prev) => !prev)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              backgroundColor: "#1a1a1a",
              color: "#ffffff",
              border: "none",
              borderRadius: 20,
              padding: "6px 14px",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            <span style={{ fontSize: 12 }}>?</span>
            {hideLabels ? "Show Granular Overlay" : "Hide Granular Overlay"}
          </button>
        </div>
      )}

      {!isMinimized && (
        <ForceGraph2D
          width={size.width}
          height={size.height}
          graphData={graphData}
          nodeColor={nodeColor}
          nodeRelSize={5}
          nodeVal={nodeVal}
          nodeLabel={nodeLabel}
          linkColor={() => "rgba(59, 130, 246, 0.25)"}
          onNodeClick={handleNodeClick}
          backgroundColor="#f5f5f5"
        />
      )}

      {!hideLabels && !isMinimized && (
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: 16,
            backgroundColor: "#ffffff",
            border: "1px solid #e2e2e2",
            borderRadius: 12,
            padding: "10px 12px",
            fontSize: 12,
            color: "#4a4a4a",
            display: "flex",
            flexDirection: "column",
            gap: 6,
            boxShadow: "0 8px 16px rgba(0, 0, 0, 0.08)",
          }}
        >
          {LEGEND_ITEMS.map((item) => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: item.color,
                  display: "inline-block",
                }}
              />
              {item.label}
            </div>
          ))}
        </div>
      )}

      {selectedNode && !isMinimized && (
        <div
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            width: 300,
            maxHeight: "80%",
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #e2e2e2",
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 12px 24px rgba(0, 0, 0, 0.12)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 12,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 15 }}>
              {TYPE_LABELS[selectedNode.type] || selectedNode.type}
            </div>
            <button
              type="button"
              onClick={() => setSelectedNode(null)}
              style={{
                border: "none",
                background: "#f2f2f2",
                borderRadius: 8,
                padding: "4px 8px",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              Close
            </button>
          </div>

          {renderFieldRows(selectedNode.data)}

          <div
            style={{
              marginTop: 12,
              fontSize: 12,
              color: "#5f5f5f",
              fontWeight: 600,
            }}
          >
            Connections: {getConnectionsCount(selectedNode.id)}
          </div>

          {loadingNeighbors && (
            <div style={{ marginTop: 8, fontSize: 12, color: "#666" }}>
              Loading related nodes...
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GraphView;
