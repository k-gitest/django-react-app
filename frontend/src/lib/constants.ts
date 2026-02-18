export const BASE_API_URL: string = import.meta.env.VITE_BASE_API_URL ?? 'http://localhost:3000';
export const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
export const SENTRY_RELEASE = import.meta.env.VITE_SENTRY_RELEASE || 'unknown';
export const IS_PRODUCTION = import.meta.env.PROD;
export const GRAPHQL_URL: string = `${BASE_API_URL}/graphql`

export const VITE_AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || '';
export const VITE_AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
export const VITE_AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE || '';