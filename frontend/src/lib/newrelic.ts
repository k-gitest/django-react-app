import { BrowserAgent } from '@newrelic/browser-agent/loaders/browser-agent';

export const initNewRelic = () => {
  // 本番環境のみ
  if (import.meta.env.PROD && import.meta.env.VITE_NEW_RELIC_LICENSE_KEY) {
    new BrowserAgent({
      init: {
        distributed_tracing: { enabled: true },
        privacy: { cookies_enabled: true },
      },
      info: {
        licenseKey: import.meta.env.VITE_NEW_RELIC_LICENSE_KEY,
        applicationID: import.meta.env.VITE_NEW_RELIC_APP_ID,
      },
    });
  }
};