import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 80,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://localhost:30001",
        changeOrigin: true,
        secure: false,
      },
      "/media": {
        target: "http://localhost:30000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: "../docker/frontend/html/dist",
    emptyOutDir: true,
  },
});
