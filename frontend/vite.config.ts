import { defineConfig, type ProxyOptions } from "vite";
import react from "@vitejs/plugin-react";

// Screens like /cart share a path with the API: browser page loads (Accept: text/html) get the app, fetches go to FastAPI.
const api: ProxyOptions = {
  target: "http://127.0.0.1:8000",
  bypass: (req) => (req.headers.accept?.includes("text/html") ? "/index.html" : undefined),
};

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/analytics": api,
      "/auth": api,
      "/capacity": api,
      "/cart": api,
      "/checkout": api,
      "/clients": api,
      "/health": api,
      "/inventory": api,
      "/me": api,
      "/products": api,
      "/profile": api,
      "/queue": api,
      "/recipes": api,
      "/recommendations": api,
      "/reports": api,
      "/shopping-list": api,
    },
  },
});
