# NeuroLens Frontend

Modern React frontend for NeuroLens - AI-Powered Retinal Disease Detection.

## Tech Stack

- **React 18+** with TypeScript
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client with JWT interceptors
- **CSS Variables** - Theming with light/dark mode support

## Getting Started

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

API requests are automatically proxied to the backend via Vite.

### Production Build

```bash
npm run build
```

Build output will be in the `dist/` directory.

## Project Structure

```
frontend/
├── public/
│   └── favicon.svg          # App favicon
├── src/
│   ├── assets/
│   │   └── logo.svg          # NeuroLens logo
│   ├── components/
│   │   ├── Loader.tsx        # Loading spinner component
│   │   ├── Navbar.tsx        # Sidebar navigation
│   │   ├── ProtectedRoute.tsx # Auth guard for routes
│   │   └── Toast.tsx         # Toast notification system
│   ├── pages/
│   │   ├── Dashboard.tsx     # Main dashboard with stats
│   │   ├── Datasets.tsx      # Dataset management UI
│   │   ├── Inference.tsx     # Inference submission & results
│   │   ├── Login.tsx         # Animated login page
│   │   └── Signup.tsx        # Animated registration page
│   ├── services/
│   │   └── api.ts            # Centralized API client with JWT
│   ├── styles/
│   │   ├── animations.css    # Keyframes and transitions
│   │   ├── base.css          # CSS variables, reset, components
│   │   └── responsive.css    # Mobile-first breakpoints
│   ├── App.tsx               # Main app with routing
│   └── main.tsx              # Entry point
├── index.html                # HTML template
├── package.json
├── tsconfig.json
└── vite.config.ts            # Vite configuration with API proxy
```

## Features

### Authentication
- JWT-based authentication with access/refresh tokens
- Auto-redirect on 401 responses
- Protected routes for authenticated users
- Animated login/signup with glassmorphism design

### Dashboard
- Real-time stats cards (datasets, inferences, status)
- System health monitoring
- Quick action cards for navigation

### Datasets
- List all uploaded datasets
- Drag & drop file upload with progress
- Dataset metadata display
- Delete confirmation dialog

### Inference
- Submit inference requests by dataset
- Real-time polling for status updates (2-second intervals)
- Results display with confidence meters
- Severity level badges (No DR to Proliferative)
- Explainability heatmaps (when available)

### UI/UX
- Responsive design (mobile-first)
- Dark/light theme toggle
- Floating particle animations on auth pages
- Smooth transitions and animations
- Toast notifications for user feedback

## API Endpoints

The frontend communicates with these backend endpoints:

| Feature | Endpoint |
|---------|----------|
| Login | `POST /api/auth/token/` |
| Register | `POST /api/auth/register/` |
| Profile | `GET /api/v1/auth/profile/` |
| Datasets | `GET/POST/DELETE /api/v1/datasets/` |
| Inference | `GET/POST /api/v1/inferences/` |
| Stats | `GET /api/v1/stats/dashboard/` |
| Health | `GET /api/health/` |

## Environment Configuration

The API base URL is configured via Vite proxy in `vite.config.ts`:

```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

## Browser Support

- Chrome 90+
- Firefox 90+
- Safari 14+
- Edge 90+

## Contributing

See [DEVELOPER_RULES.md](../DEVELOPER_RULES.md) for development guidelines.
