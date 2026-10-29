import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_API_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { "@": path.resolve(import.meta.dirname, "./src") },
    },
    build: {
      rolldownOptions: {
        output: {
          // Tách vendor thành chunk riêng: đổi code app không làm mất cache của thư viện
          codeSplitting: {
            groups: [
              { name: "react", test: /node_modules[\\/](react|react-dom|scheduler|react-router)[\\/]/ },
              { name: "data", test: /node_modules[\\/](@tanstack|axios|zustand)[\\/]/ },
              { name: "forms", test: /node_modules[\\/](react-hook-form|@hookform|zod)[\\/]/ },
            ],
          },
        },
      },
    },
    server: {
      port: 5173,
      // Proxy /api → FastAPI để dev không bị chặn CORS (backend chưa bật CORSMiddleware)
      proxy: {
        "/api": { target: apiTarget, changeOrigin: true },
        "/health": { target: apiTarget, changeOrigin: true },
      },
    },
  };
});
