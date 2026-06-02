import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import badge from "./assets/SethuAI_badge.png";
import "./index.css";

// Favicon (uses the bundled, hashed asset URL — served by the /assets mount).
const link = (document.querySelector("link[rel='icon']") ??
  document.createElement("link")) as HTMLLinkElement;
link.rel = "icon";
link.href = badge;
document.head.appendChild(link);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
