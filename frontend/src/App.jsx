import React from "react";
import GraphView from "./GraphView.jsx";
import ChatPanel from "./ChatPanel.jsx";

const App = () => {
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
        <GraphView />
      </div>
      <div
        style={{
          width: "35%",
          height: "100%",
          borderLeft: "1px solid #e6e6e6",
        }}
      >
        <ChatPanel />
      </div>
    </div>
  );
};

export default App;
