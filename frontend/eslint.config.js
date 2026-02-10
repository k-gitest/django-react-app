import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'
import relay from 'eslint-plugin-relay';

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    plugins: {
      relay, // Relay用のESLintプラグイン
    },
    rules: {
      // 全体的なルール
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true }, // 定数のエクスポートを許可する設定を追加
      ],
      // Relayのルール
      ...relay.configs.recommended.rules, // Relayの推奨ルールを有効化
      'relay/generated-flow-types': 'off', // TypeScript環境なので必須
      'relay/graphql-naming': 'error',    // 命名規則 {Module}_{prop} を強制
      'relay/must-colocate-fragment-spreads': 'warn', // コンポーネントと同じ場所にSpreadを書く
    },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
  // UIコンポーネント専用のオーバーライド設定を追加
  {
    files: ['src/components/ui/**/*.{ts,tsx}'],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
])
