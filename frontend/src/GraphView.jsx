import React, { useEffect, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TYPE_COLORS = {
  sales_order_header: "#2f6bff",
  billing_document_header: "#ff7a45",
  product: "#00a88f",
  business_partner: "#6f42c1",
  payment: "#f4c20d",
  journal_entry_item: "#ff4d8d",
  outbound_delivery_header: "#1b998b",
};

const GraphView = () => {
  const containerRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [size, setSize] = useState({ width: 400, height: 400 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loadingNeighbors, setLoadingNeighbors] = useState(false);

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
        setGraphData({
          nodes: data.nodes || [],
          links: (data.edges || []).map((edge) => ({
            source: edge.source,
            target: edge.target,
          })),
        });
      } catch (error) {
        setGraphData({ nodes: [], links: [] });
      }
    };

    fetchGraph();
  }, []);

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

  const nodeColor = (node) => TYPE_COLORS[node.type] || "#8c8c8c";

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        backgroundColor: "#ffffff",
      }}
    >
      <ForceGraph2D
        width={size.width}
        height={size.height}
        graphData={graphData}
        nodeColor={nodeColor}
        linkColor={() => "rgba(0,0,0,0.12)"}
        nodeRelSize={5}
        onNodeClick={handleNodeClick}
      />

      {selectedNode && (
        <div
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            width: 320,
            maxHeight: "80%",
            overflowY: "auto",
            background: "#ffffff",
            border: "1px solid #e2e2e2",
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 10px 24px rgba(0, 0, 0, 0.12)",
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
            <div style={{ fontWeight: 600 }}>Node Details</div>
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

          <div style={{ marginBottom: 8 }}>
            <strong>Type:</strong> {selectedNode.type}
          </div>
          <div style={{ marginBottom: 12 }}>
            <strong>ID:</strong> {selectedNode.id}
          </div>

          {Object.entries(selectedNode.data).map(([key, value]) => (
            <div key={key} style={{ marginBottom: 6, fontSize: 14 }}>
              <span style={{ color: "#555", fontWeight: 500 }}>{key}:</span>{" "}
              <span>{value === null || value === undefined || value === "" ? "-" : String(value)}</span>
            </div>
          ))}

          {loadingNeighbors && (
            <div style={{ marginTop: 12, fontSize: 12, color: "#666" }}>
              Loading related nodes...
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GraphView;
