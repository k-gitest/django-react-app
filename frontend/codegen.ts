import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  // バックエンドで生成した schema.graphql を参照
  // (frontend/ ディレクトリから見て 1つ上にある前提)
  schema: '../schema.graphql',

  // クエリやミューテーションが書かれたファイルを探す場所
  documents: 'src/graphql/**/*.ts',

  generates: {
    'src/graphql/types.ts': {
      plugins: [
        'typescript',
        'typescript-operations',
      ],
      config: {
        // 基本設定
        skipTypename: false,
        withHooks: false,
        withComponent: false,

        // 型を厳密にするための設定
        arrayInputCoercion: false,

        // スカラー型のマッピング
        scalars: {
          DateTime: 'string',
        },
      },
    },
  },
};

export default config;