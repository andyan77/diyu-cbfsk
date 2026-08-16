import { expect, test } from "@playwright/test";

// 与 docker-compose.yml 的 bootstrap 取值一致。这是本地开发栈的账号，
// 生产账号由 deploy/provision_cbfsk.sh 现场生成，永不复用这里的取值。
const USERNAME = process.env.E2E_USERNAME ?? "cbfsk-ops";
const SECRET = process.env.E2E_SECRET ?? "cbfsk.ops.local";

const stamp = Date.now().toString(36);

test("登录 → 创建租户 → 创建品牌 → 创建草稿任务", async ({ page }) => {
  await page.goto("/app/");

  await page.getByTestId("login-username").fill(USERNAME);
  await page.getByTestId("login-password").fill(SECRET);
  await page.getByTestId("login-submit").click();

  await expect(page.getByTestId("session-username")).toHaveText(USERNAME);

  const slug = `e2e-${stamp}`;
  await page.getByTestId("tenant-slug").fill(slug);
  await page.getByTestId("tenant-name").fill(`E2E 租户 ${stamp}`);
  await page.getByTestId("tenant-create").click();
  await expect(page.getByTestId("session-tenant")).toHaveText(`E2E 租户 ${stamp}`);

  const brandCode = `BR${stamp}`;
  await page.getByTestId("brand-code").fill(brandCode);
  await page.getByTestId("brand-name").fill(`E2E 品牌 ${stamp}`);
  await page.getByTestId("brand-create").click();
  await expect(page.getByTestId("brand-table").getByText(brandCode)).toBeVisible();

  await page.getByTestId("task-brand").click();
  await page.getByText(`E2E 品牌 ${stamp}`, { exact: true }).last().click();
  const title = `E2E 任务 ${stamp}`;
  await page.getByTestId("task-title").fill(title);
  await page.getByTestId("task-create").click();
  await expect(page.getByTestId("task-table").getByText(title)).toBeVisible();
});

test("未登录时工作台不泄露任何租户数据", async ({ page }) => {
  const response = await page.request.get("/api/brands");
  expect(response.status()).toBe(401);
});
