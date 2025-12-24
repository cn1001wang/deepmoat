import eslintConfig from '@antfu/eslint-config'

export default eslintConfig({
  // Type of the project. 'lib' for libraries, the default is 'app'
  type: 'lib',

  // Or customize the stylistic rules
  // stylistic: {
  //   indent: 2, // 4, or 'tab'
  //   quotes: 'single', // or 'double'
  // },

  // // TypeScript and Vue are autodetected, you can also explicitly enable them:
  // typescript: true,
  // vue: true,

  // // Disable jsonc and yaml support
  // jsonc: false,
  // yaml: false,

  ignores: [
    'types/auto-imports.d.ts',
    'types/components.d.ts',
    'public',
    'tsconfig.*.json',
    'tsconfig.json',
  ],
}, {
  rules: {
    'no-console': 0,
    'style/quote-props': 2,
    'ts/no-unused-expressions': 1,
    'unused-imports/no-unused-vars': 0,
    'ts/no-empty-object-type': 0,
    'node/prefer-global/process': 0,
    'ts/no-unsafe-function-type': 0,
    '@typescript-eslint/no-duplicate-enum-values': 0,
    'ts/no-non-null-asserted-optional-chain': 0,
    'regexp/no-unused-capturing-group': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    '@typescript-eslint/explicit-function-return-type': [
      0,
      {
        allowExpressions: true, // 允许函数表达式不显式写返回类型
        allowTypedFunctionExpressions: true,
        allowHigherOrderFunctions: true,
        allowDirectConstAssertionInArrowFunctions: true,
        allowConciseArrowFunctionExpressionsStartingWithVoid: true,
        allowFunctionsWithoutTypeParameters: true,
        // allowFunctionsWithoutReturnTypeWhenUseful: true, // ✅ 关键项
      },
    ],
    // 'vue/block-order': ['error', {
    //   'order': ['template', 'script', 'style'],
    // }],
  },
})
