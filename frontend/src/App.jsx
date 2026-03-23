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
        width: "100vw",
        height: "100vh",
        backgroundColor: "#ffffff",
        margin: 0,
        padding: 0,
      }}
    >
      <div style={{ width: "65%", height: "100%" }}>
        <GraphView
          highlightedIds={highlightedIds}
          onGraphData={setGraphData}
        />
      </div>
      <div
        style={{
          width: "35%",
          height: "100%",
          borderLeft: "1px solid #e6e6e6",
        }}
      >
        <ChatPanel onAnswer={handleAnswer} />
      </div>
    </div>
  );
};

export default App;
