# 🚀 MACROCOMM BI PLATFORM - FRONTEND

## State-of-the-Art React + Next.js 14 Frontend

A ChatGPT-like interface for business intelligence that combines document Q&A with powerful data visualization.

---

## 🎨 Design Philosophy

**Aesthetic Direction**: **Premium Dark Tech** - A refined, professional interface that feels premium without being flashy. Think Bloomberg Terminal meets modern SaaS.

**Brand Colors**:
- Primary: Sunset Orange `#FF6E00`
- Accent: Bright Orange `#FF923F`
- Background: Deep Navy `#0A0F1C`
- Surface: Slate `#1A1F2E`
- Text: Silver `#E2E8F0`

**Typography**:
- Display: `Cal Sans` (distinctive headings)
- Body: `Instrument Sans` (clean, readable)
- Code: `JetBrains Mono` (technical content)

---

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js 14 App Router
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Landing/Home page
│   ├── globals.css              # Global styles + Tailwind
│   ├── (auth)/                  # Auth routes (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/             # Protected dashboard routes
│   │   ├── layout.tsx           # Dashboard layout with sidebar
│   │   ├── chat/page.tsx        # Main chat interface
│   │   ├── dashboards/          # Dashboard management
│   │   │   ├── page.tsx         # List dashboards
│   │   │   └── [id]/page.tsx    # View/edit dashboard
│   │   ├── documents/page.tsx   # Document management
│   │   └── settings/page.tsx    # User settings
│   └── api/                     # API routes (if needed)
│
├── components/                   # React components
│   ├── ui/                      # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   ├── chat/                    # Chat-specific components
│   │   ├── ChatInterface.tsx    # Main chat container
│   │   ├── ChatMessage.tsx      # Individual message
│   │   ├── ChatInput.tsx        # Input with file upload
│   │   ├── MessageList.tsx      # Scrollable message list
│   │   └── StreamingText.tsx    # Animated streaming response
│   ├── dashboard/               # Dashboard components
│   │   ├── DashboardBuilder.tsx # Drag-and-drop builder
│   │   ├── DashboardGrid.tsx    # react-grid-layout wrapper
│   │   ├── WidgetCard.tsx       # Individual widget container
│   │   └── WidgetPicker.tsx     # Widget selection modal
│   ├── charts/                  # Chart components
│   │   ├── ChartContainer.tsx   # Universal chart wrapper
│   │   ├── BarChart.tsx
│   │   ├── LineChart.tsx
│   │   ├── PieChart.tsx
│   │   ├── ScatterChart.tsx
│   │   ├── KPICard.tsx
│   │   └── InsightCard.tsx
│   ├── upload/                  # File upload components
│   │   ├── FileUpload.tsx       # Drag-and-drop upload
│   │   ├── FilePreview.tsx      # Preview uploaded files
│   │   └── ProgressBar.tsx      # Upload progress
│   ├── layout/                  # Layout components
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   ├── Header.tsx           # Top header
│   │   ├── Logo.tsx             # Macrocomm logo
│   │   └── ThemeToggle.tsx      # Dark/light mode
│   └── shared/                  # Shared components
│       ├── LoadingSpinner.tsx
│       ├── EmptyState.tsx
│       ├── ErrorBoundary.tsx
│       └── AnimatedGradient.tsx
│
├── lib/                         # Utilities and configurations
│   ├── api/                     # API client
│   │   ├── client.ts            # Axios/fetch wrapper
│   │   ├── endpoints.ts         # API endpoint definitions
│   │   └── types.ts             # API response types
│   ├── hooks/                   # Custom React hooks
│   │   ├── useChat.ts           # Chat state and actions
│   │   ├── useSession.ts        # Analysis session
│   │   ├── useDashboard.ts      # Dashboard state
│   │   ├── useFileUpload.ts     # File upload handling
│   │   └── useStreamingResponse.ts  # SSE/WebSocket streaming
│   ├── stores/                  # Zustand state stores
│   │   ├── chatStore.ts         # Chat messages state
│   │   ├── sessionStore.ts      # Session management
│   │   ├── dashboardStore.ts    # Dashboard state
│   │   └── uiStore.ts           # UI state (modals, sidebar)
│   ├── utils/                   # Utility functions
│   │   ├── formatters.ts        # Number, date formatters
│   │   ├── validators.ts        # Input validation
│   │   └── cn.ts                # Classname utility
│   └── constants.ts             # App constants
│
├── types/                       # TypeScript type definitions
│   ├── api.ts                   # API types
│   ├── chat.ts                  # Chat types
│   ├── dashboard.ts             # Dashboard types
│   ├── chart.ts                 # Chart types
│   └── index.ts                 # Re-exports
│
├── styles/                      # Additional styles
│   └── animations.css           # Custom animations
│
├── public/                      # Static assets
│   ├── logo.svg
│   ├── favicon.ico
│   └── fonts/
│
├── package.json
├── tailwind.config.ts
├── next.config.js
├── tsconfig.json
└── .env.local
```

---

## 🛠 Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Framework** | Next.js 14 | App Router, SSR, API routes |
| **Language** | TypeScript | Type safety |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Components** | shadcn/ui | Accessible UI components |
| **Charts** | Tremor + Recharts | Data visualization |
| **Dashboard** | react-grid-layout | Drag-and-drop grid |
| **State** | Zustand | Simple state management |
| **Data Fetching** | TanStack Query | Server state management |
| **Animations** | Framer Motion | Smooth animations |
| **Forms** | React Hook Form + Zod | Form handling |
| **Icons** | Lucide React | Beautiful icons |
| **Fonts** | next/font | Optimized fonts |

---

## 🚀 Quick Start

```bash
# 1. Create Next.js project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false

# 2. Navigate to project
cd frontend

# 3. Install dependencies
npm install zustand @tanstack/react-query framer-motion react-grid-layout @tremor/react recharts lucide-react class-variance-authority clsx tailwind-merge zod react-hook-form @hookform/resolvers

# 4. Install shadcn/ui
npx shadcn-ui@latest init

# 5. Add shadcn components
npx shadcn-ui@latest add button card input dialog dropdown-menu toast avatar badge separator scroll-area tabs tooltip

# 6. Set environment variables
cp .env.example .env.local

# 7. Start development server
npm run dev
```

---

## 🎯 Key Features

### 1. Chat Interface
- Natural language queries
- Real-time streaming responses
- File upload with drag-and-drop
- Message history with search
- Code syntax highlighting

### 2. Dashboard Builder
- Drag-and-drop widgets
- Resizable panels
- 84 chart types
- Auto-layout suggestions
- Export to PDF/PNG

### 3. Data Analysis
- Automatic data profiling
- Statistical analysis
- Trend detection
- Anomaly detection
- Forecasting

### 4. AI Insights
- AI-generated insights
- Chart explanations
- Recommendations
- Natural language summaries

---

## 📦 Package.json

```json
{
  "name": "macrocomm-bi-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "framer-motion": "^10.18.0",
    "react-grid-layout": "^1.4.4",
    "@tremor/react": "^3.14.0",
    "recharts": "^2.10.4",
    "lucide-react": "^0.303.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "zod": "^3.22.4",
    "react-hook-form": "^7.49.2",
    "@hookform/resolvers": "^3.3.2",
    "date-fns": "^3.0.6",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "@types/node": "^20.10.6",
    "@types/react": "^18.2.46",
    "@types/react-dom": "^18.2.18",
    "@types/react-grid-layout": "^1.3.5",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-config-next": "14.0.4",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.3"
  }
}
```

---

## 🔗 Backend Integration

The frontend connects to the FastAPI backend at:
- **Development**: `http://localhost:8000`
- **Production**: `https://api.macrocomm.ai`

### API Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | POST | Create analysis session |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/sessions/{id}/upload` | POST | Upload file to session |
| `/api/sessions/{id}/query` | POST | Natural language query |
| `/api/dashboards` | GET/POST | Dashboard CRUD |
| `/api/dashboards/{id}` | GET/PUT/DELETE | Single dashboard |
| `/api/export/{id}` | GET | Export dashboard |

### WebSocket:
- `/ws/chat/{session_id}` - Real-time chat with streaming

---

## 🎨 Design Tokens

```css
:root {
  /* Brand Colors */
  --color-primary: #FF6E00;
  --color-primary-light: #FF923F;
  --color-primary-dark: #E65100;
  
  /* Background */
  --color-bg-primary: #0A0F1C;
  --color-bg-secondary: #1A1F2E;
  --color-bg-tertiary: #252B3B;
  
  /* Text */
  --color-text-primary: #F1F5F9;
  --color-text-secondary: #94A3B8;
  --color-text-muted: #64748B;
  
  /* Borders */
  --color-border: #334155;
  --color-border-light: #475569;
  
  /* Status */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 40px rgba(255, 110, 0, 0.15);
}
```

---

## 🏗 Development Phases

### Phase 2A: Core Setup (Day 1-2)
- [x] Project scaffolding
- [ ] Tailwind configuration
- [ ] shadcn/ui setup
- [ ] Type definitions
- [ ] API client
- [ ] State stores

### Phase 2B: Layout & Navigation (Day 3-4)
- [ ] Root layout
- [ ] Sidebar navigation
- [ ] Header with user menu
- [ ] Theme switching
- [ ] Responsive design

### Phase 2C: Chat Interface (Day 5-7)
- [ ] Message list component
- [ ] Chat input with upload
- [ ] Streaming response handler
- [ ] Message formatting (markdown)
- [ ] Code syntax highlighting

### Phase 2D: Data Visualization (Day 8-10)
- [ ] Chart components
- [ ] KPI cards
- [ ] Dashboard grid
- [ ] Widget drag-and-drop
- [ ] Export functionality

### Phase 2E: Polish & Deploy (Day 11-14)
- [ ] Animations
- [ ] Error handling
- [ ] Loading states
- [ ] Performance optimization
- [ ] Vercel deployment

---

*Document Version: 1.0*
*Created: December 2024*
*Author: Macrocomm Development Team*
