import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Workbench } from "./Workbench";

// 挂载模式：单一 root、StrictMode 开启、语言固定 zh-CN。
// 首版不使用 React Server Components（PRD 附录 D：RSC 多次安全公告，首版不用）。
const container = document.getElementById("root");
if (!container) {
  throw new Error("ROOT_CONTAINER_MISSING");
}

createRoot(container).render(
  <StrictMode>
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <Workbench />
      </AntApp>
    </ConfigProvider>
  </StrictMode>
);
