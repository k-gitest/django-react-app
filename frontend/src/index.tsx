import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initNewRelic } from './lib/newrelic';
import * as Sentry from "@sentry/react";
import { SENTRY_DSN, SENTRY_RELEASE, IS_PRODUCTION, BASE_API_URL } from "@/lib/constants";
import { Auth0Provider } from './lib/auth0-provider';


// Sentryの初期化
if (IS_PRODUCTION && SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    sendDefaultPii: true,
    environment: import.meta.env.MODE,
    release: SENTRY_RELEASE,

    // 分散トレーシング設定（重要！）
    integrations: [
      Sentry.browserTracingIntegration(),
    ],

    // Django APIのドメインを指定（Trace IDを送信）
    tracePropagationTargets: [
      "localhost",
      /^https:\/\/.*\.onrender\.com\/api/,  // Render本番
      BASE_API_URL,  // 環境変数から動的に取得
    ],

    tracesSampleRate: 0.1,
  });

  // グローバルに公開（setSentryUserで使用するため）
  window.Sentry = Sentry;
}

// Sentry初期化の後に
initNewRelic();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Auth0Provider>
      <App />
    </Auth0Provider>
  </React.StrictMode>,
);
