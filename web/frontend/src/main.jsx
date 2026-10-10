import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import KoodalApp from "./KoodalApp.jsx";
import LiveGuest from './LiveGuest.jsx'
const isGuest = window.location.pathname.startsWith('/r/')
   // in the render call: {isGuest ? <LiveGuest /> : <App />}
createRoot(document.getElementById("root")).render(
  <StrictMode>
    {isGuest ? <LiveGuest /> : <KoodalApp />}
  </StrictMode>
);
