import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// base 由后端挂载路径决定：runtime/api/main.py 的 STATIC_MOUNT_PATH 是 /app。
// 两处不一致时，构建出来的页面能打开但刷新会 404——dev server 下看不出来。
export default defineConfig({
  base: "/app/",
  plugins: [react()],
  esbuild: { jsx: "automatic" },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets",
    sourcemap: false,
    rollupOptions: {
      output: {
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]"
      }
    }
  },
  server: {
    port: 18100,
    proxy: {
      "/api": { target: "http://127.0.0.1:18000", changeOrigin: false }
    }
  }
});
