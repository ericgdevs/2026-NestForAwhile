import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/analytics": "http://127.0.0.1:8000",
      "/auth": "http://127.0.0.1:8000",
      "/capacity": "http://127.0.0.1:8000",
      "/cart": "http://127.0.0.1:8000",
      "/checkout": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/inventory": "http://127.0.0.1:8000",
      "/me": "http://127.0.0.1:8000",
      "/products": "http://127.0.0.1:8000",
      "/profile": "http://127.0.0.1:8000",
      "/queue": "http://127.0.0.1:8000",
      "/recipes": "http://127.0.0.1:8000",
      "/recommendations": "http://127.0.0.1:8000",
      "/reports": "http://127.0.0.1:8000",
    },
  },
});
