import { test as base, expect } from '@playwright/test';
import { http } from 'msw';
import type { MockServiceWorker } from 'playwright-msw';
import { createWorkerFixture } from 'playwright-msw';

import { authHandlers } from '@tests/mocks/auth.handlers';

const test = base.extend<{
  worker: MockServiceWorker;
  http: typeof http;
}>({
  worker: createWorkerFixture(authHandlers),
  http,
});

export { expect, test };
