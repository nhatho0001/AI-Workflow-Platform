# AI Workflow Platform — Web

Frontend SPA cho AI Workflow Platform: **TypeScript + React 19 + Vite**, Tailwind CSS v4, TanStack Query, Zustand, React Router, react-hook-form + zod.

## Chạy dev

```bash
cd web
npm install
cp .env.example .env      # nếu chưa có
npm run dev               # http://localhost:5173
```

Backend FastAPI phải chạy ở `http://localhost:8000` (đổi bằng `VITE_API_PROXY_TARGET`). Vite proxy chuyển `/api/*` sang backend nên dev không cần CORS.

## Chạy bằng Docker

Từ thư mục gốc repo:

```bash
docker compose --env-file server/.env up -d --build
# Web:  http://localhost:3000   (nginx: phục vụ SPA + proxy /api → server:8000)
# API:  http://localhost:8000/docs
```

Image được build 2 stage (`web/Dockerfile`): Node build ra `dist/`, sau đó nginx phục vụ (`web/nginx.conf`). Vì nginx proxy `/api` nên frontend và API cùng origin, không cần CORS. SSE chat đã được tắt buffer.

Biến `VITE_*` được nhúng vào bundle **lúc build**: đổi giá trị thì phải `--build` lại. `VITE_DEFAULT_MODEL_ID` lấy từ biến môi trường cùng tên khi chạy compose.

Container chạy bản production và không có hot reload. Khi code UI, nên chạy `npm run dev` ở máy (vẫn dùng backend trong Docker ở cổng 8000).

| Lệnh | Mô tả |
|---|---|
| `npm run dev` | Dev server + HMR |
| `npm run build` | Typecheck + build production vào `dist/` |
| `npm run lint` | ESLint |
| `npm run typecheck` | Chỉ chạy TypeScript |
| `npm run format` | Prettier (tự sắp xếp class Tailwind) |

## Cấu trúc

```
src/
├── app/                # Ghép ứng dụng: providers, router, layouts, route guards, menu
│   ├── navigation.ts   # Danh sách menu (lọc theo role)
│   ├── router.tsx      # Toàn bộ route
│   ├── layouts/        # AppLayout (sidebar), AuthLayout
│   └── routes/         # ProtectedRoute, GuestRoute, RequireRole
├── features/           # Mỗi domain một thư mục — khớp với server/app/modules/
│   ├── auth/           # login / register / logout, auth store
│   ├── users/          # profile, quản lý user (admin)
│   └── chat/           # conversations, messages, streaming SSE
├── components/
│   ├── ui/             # Primitive kiểu shadcn/ui (button, input, card…)
│   └── common/         # Component dùng chung có logic nhỏ (spinner, form-field)
├── lib/                # api-client (axios + tự refresh token), sse, query-client, utils
├── config/env.ts       # Điểm duy nhất đọc import.meta.env
├── pages/              # Trang không thuộc feature nào (404, error)
└── styles/index.css    # Tailwind + design tokens
```

Mỗi feature có cùng một khung:

```
features/<name>/
├── types.ts        # Type + zod schema, khớp với Pydantic schema ở backend
├── api.ts          # Hàm gọi HTTP thuần (không React)
├── hooks.ts        # React Query hooks + query keys
├── components/     # Component riêng của feature
├── pages/          # Trang gắn vào router
└── index.ts        # Public API — nơi khác CHỈ import từ "@/features/<name>"
```

ESLint chặn import sâu kiểu `@/features/chat/components/...` từ bên ngoài feature, để các feature tách bạch với nhau.

## Thêm một feature mới (ví dụ `workflows`)

1. Tạo `src/features/workflows/` theo khung trên.
2. Export trang trong `index.ts`.
3. Thêm route vào `src/app/router.tsx`. Feature lớn nên dùng `lazy: () => import("@/features/workflows").then(m => ({ Component: m.WorkflowsPage }))` để tách chunk.
4. Thêm một dòng vào `NAV_ITEMS` trong `src/app/navigation.ts`.
5. Thêm UI primitive khi cần: `npx shadcn@latest add dialog dropdown-menu ...` (đã có `components.json`).

Gợi ý thư viện cho roadmap: `@xyflow/react` (workflow editor kéo-thả), `react-markdown` + `shiki` (render câu trả lời LLM).

## Ghi chú về backend hiện tại

- **Auth**: token nằm trong body response và được lưu ở `localStorage`. Khi gặp 401, `api-client` tự gọi `/auth/refresh` (mỗi lần chỉ chạy một request refresh) rồi gửi lại request cũ. Nếu refresh thất bại thì đăng xuất.
- **Chat streaming**: `/chat/start` và `/chat/conversations/{id}/messages` là POST trả SSE, nên `lib/sse.ts` đọc stream bằng `fetch` (vì `EventSource` không gửi được POST hay header `Authorization`).
- **`model_id`**: backend bắt buộc trường này nhưng chưa có API danh sách model, nên tạm lấy từ `VITE_DEFAULT_MODEL_ID`.
- **LLM chưa được nối**: assistant message hiện có content rỗng, giao diện hiển thị ghi chú thay vì để trống.
- **Production**: backend chưa bật `CORSMiddleware`. Khi deploy hãy phục vụ frontend và API cùng domain (reverse proxy `/api` → FastAPI), hoặc bật CORS ở backend.
