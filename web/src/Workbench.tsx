import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Form,
  Input,
  Layout,
  Select,
  Space,
  Table,
  Typography
} from "antd";
import { useCallback, useEffect, useState } from "react";

import { client, type BrandOut, type DraftTaskOut, type SessionOut, type TenantOut } from "./client";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function Workbench() {
  const [session, setSession] = useState<SessionOut | null>(null);
  const [tenants, setTenants] = useState<TenantOut[]>([]);
  const [brands, setBrands] = useState<BrandOut[]>([]);
  const [tasks, setTasks] = useState<DraftTaskOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const next = await client.readSession();
    setSession(next);
    if (!next.user) {
      setTenants([]);
      setBrands([]);
      setTasks([]);
      return;
    }
    setTenants(await client.listTenants());
    if (next.active_tenant) {
      setBrands(await client.listBrands());
      setTasks(await client.listDraftTasks());
    } else {
      setBrands([]);
      setTasks([]);
    }
  }, []);

  useEffect(() => {
    refresh().catch((err: unknown) => setError(errorText(err)));
  }, [refresh]);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
    } catch (err: unknown) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ background: "#001529" }}>
        <Title level={4} style={{ color: "#fff", margin: 0, lineHeight: "64px" }}>
          笛语跨品牌搭配 · 工作台
        </Title>
      </Header>
      <Content style={{ padding: 24, maxWidth: 960, margin: "0 auto", width: "100%" }}>
        {error && (
          <Alert
            type="error"
            showIcon
            message={error}
            data-testid="error-banner"
            style={{ marginBottom: 16 }}
          />
        )}

        {!session?.user ? (
          <Card title="登录" data-testid="login-card">
            <Form
              layout="vertical"
              onFinish={(values: { username: string; password: string }) =>
                run(() => client.login(values.username, values.password))
              }
            >
              <Form.Item label="账号" name="username" rules={[{ required: true }]}>
                <Input data-testid="login-username" autoComplete="username" />
              </Form.Item>
              <Form.Item label="口令" name="password" rules={[{ required: true }]}>
                <Input.Password data-testid="login-password" autoComplete="current-password" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={busy} data-testid="login-submit">
                登录
              </Button>
            </Form>
          </Card>
        ) : (
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Card
              title="当前会话"
              data-testid="session-card"
              extra={
                <Button onClick={() => run(() => client.logout())} data-testid="logout">
                  登出
                </Button>
              }
            >
              <Descriptions column={1} size="small">
                <Descriptions.Item label="账号">
                  <span data-testid="session-username">{session.user.username}</span>
                </Descriptions.Item>
                <Descriptions.Item label="当前租户">
                  <span data-testid="session-tenant">
                    {session.active_tenant ? session.active_tenant.display_name : "未选择"}
                  </span>
                </Descriptions.Item>
              </Descriptions>
              <Text type="secondary">
                租户上下文由服务端会话固化，前端不持有、也不发送 tenant_id。
              </Text>
            </Card>

            <Card title="租户" data-testid="tenant-card">
              <Form
                layout="inline"
                onFinish={(values: { slug: string; displayName: string }) =>
                  run(() => client.createTenant(values.slug, values.displayName))
                }
              >
                <Form.Item name="slug" rules={[{ required: true }]}>
                  <Input placeholder="租户标识（小写字母数字与短横）" data-testid="tenant-slug" />
                </Form.Item>
                <Form.Item name="displayName" rules={[{ required: true }]}>
                  <Input placeholder="租户名称" data-testid="tenant-name" />
                </Form.Item>
                <Button type="primary" htmlType="submit" loading={busy} data-testid="tenant-create">
                  创建租户
                </Button>
              </Form>
              <Divider />
              <Select
                style={{ minWidth: 280 }}
                placeholder="切换当前租户"
                value={session.active_tenant?.id}
                data-testid="tenant-select"
                onChange={(value: string) => run(() => client.selectTenant(value))}
                options={tenants.map((t) => ({ value: t.id, label: `${t.display_name}（${t.role}）` }))}
              />
            </Card>

            <Card title="品牌" data-testid="brand-card">
              <Form
                layout="inline"
                onFinish={(values: { code: string; displayName: string }) =>
                  run(() => client.createBrand(values.code, values.displayName))
                }
              >
                <Form.Item name="code" rules={[{ required: true }]}>
                  <Input placeholder="品牌代号" data-testid="brand-code" />
                </Form.Item>
                <Form.Item name="displayName" rules={[{ required: true }]}>
                  <Input placeholder="品牌名称" data-testid="brand-name" />
                </Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={busy}
                  disabled={!session.active_tenant}
                  data-testid="brand-create"
                >
                  创建品牌
                </Button>
              </Form>
              <Divider />
              <Table
                size="small"
                rowKey="id"
                pagination={false}
                dataSource={brands}
                data-testid="brand-table"
                columns={[
                  { title: "代号", dataIndex: "code" },
                  { title: "名称", dataIndex: "display_name" }
                ]}
              />
            </Card>

            <Card title="草稿任务" data-testid="task-card">
              <Form
                layout="inline"
                onFinish={(values: { brandId: string; title: string }) =>
                  run(() => client.createDraftTask(values.brandId, values.title))
                }
              >
                <Form.Item name="brandId" rules={[{ required: true }]}>
                  <Select
                    style={{ minWidth: 200 }}
                    placeholder="选择品牌"
                    data-testid="task-brand"
                    options={brands.map((b) => ({ value: b.id, label: b.display_name }))}
                  />
                </Form.Item>
                <Form.Item name="title" rules={[{ required: true }]}>
                  <Input placeholder="任务标题" data-testid="task-title" />
                </Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={busy}
                  disabled={!session.active_tenant}
                  data-testid="task-create"
                >
                  创建任务
                </Button>
              </Form>
              <Divider />
              <Table
                size="small"
                rowKey="id"
                pagination={false}
                dataSource={tasks}
                data-testid="task-table"
                columns={[
                  { title: "标题", dataIndex: "title" },
                  { title: "状态", dataIndex: "status" }
                ]}
              />
            </Card>
          </Space>
        )}
      </Content>
    </Layout>
  );
}
