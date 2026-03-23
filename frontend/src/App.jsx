import React, { useRef, useState } from "react";
import GraphView from "./GraphView.jsx";
import ChatPanel from "./ChatPanel.jsx";

const App = () => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [highlightedIds, setHighlightedIds] = useState([]);
  const clearTimerRef = useRef(null);

  const handleAnswer = (answer) => {
    if (!answer) {
      setHighlightedIds([]);
      return;
    }

    const text = String(answer).toLowerCase();
    const matches = [];
    const nodes = graphData?.nodes || [];

    nodes.forEach((node) => {
      if (!node) {
        return;
      }

      const nodeId = node.id ? String(node.id) : "";
      let matched = false;

      if (nodeId && text.includes(nodeId.toLowerCase())) {
        matched = true;
      }

      if (!matched && node.data) {
        for (const value of Object.values(node.data)) {
          if (value === null || value === undefined) {
            continue;
          }
          const valueText = String(value).toLowerCase();
          if (valueText && text.includes(valueText)) {
            matched = true;
            break;
          }
        }
      }

      if (matched && nodeId) {
        matches.push(nodeId);
      }
    });

    setHighlightedIds(matches);

    if (clearTimerRef.current) {
      clearTimeout(clearTimerRef.current);
    }

    clearTimerRef.current = setTimeout(() => {
      setHighlightedIds([]);
    }, 10000);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100vw",
        height: "100vh",
        backgroundColor: "#f5f5f5",
      }}
    >
      <header
        style={{
          height: 48,
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e0e0e0",
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          fontFamily: "Inter, system-ui, sans-serif",
          fontSize: 14,
        }}
      >
        <span style={{ color: "#8b8b8b", marginRight: 6 }}>Mapping /</span>
        <span style={{ color: "#111111", fontWeight: 600 }}>Order to Cash</span>
      </header>

      <div style={{ flex: 1, display: "flex" }}>
        <div style={{ width: "65%", height: "100%" }}>
          <GraphView highlightedIds={highlightedIds} onGraphData={setGraphData} />
        </div>
        <div
          style={{
            width: "35%",
            height: "100%",
            borderLeft: "1px solid #e0e0e0",
            backgroundColor: "#f5f5f5",
          }}
        >
          <ChatPanel onAnswer={handleAnswer} />
        </div>
      </div>
    </div>
  );
};

export default App;
