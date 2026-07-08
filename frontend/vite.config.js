import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    base: "./",
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: env.VITE_API_BASE || "http://localhost:8080",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, "")
        },
        "/ai": {
          target: env.VITE_AI_BASE || "http://localhost:5000",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ai/, "")
        },
        "/media": {
          target: env.VITE_NGINX_BASE || "http://localhost:9092",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/media/, "")
        }
      }
    }
  };
});
