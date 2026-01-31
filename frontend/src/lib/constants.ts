export const BASE_API_URL: string = import.meta.env.VITE_BASE_API_URL ?? 'http://localhost:3000';
export const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
export const SENTRY_RELEASE = import.meta.env.VITE_SENTRY_RELEASE || 'unknown';
export const IS_PRODUCTION = import.meta.env.PROD;
export const GRAPHQL_URL: string = `${BASE_API_URL}/graphql`