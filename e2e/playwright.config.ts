import { defineConfig, devices } from "@playwright/test";

// 目标地址由外部给定：本地是 docker compose 起的 127.0.0.1:18000，
// CI 是 runtime-ci.yml 里起的同一个应用。E2E 不自己拉起后端——
// 让它内嵌一套启动逻辑，就会出现「E2E 能过但 compose 起不来」的分叉。
const baseURL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:18000";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"]
  }
});
