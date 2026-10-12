/**
 * ESLint 9 flat config. Ishga tushirish: npx eslint js tests sw.js
 */
export default [
  {
    files: ['js/**/*.js', 'tests/**/*.mjs', 'sw.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        location: 'readonly',
        localStorage: 'readonly',
        fetch: 'readonly',
        console: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        requestAnimationFrame: 'readonly',
        cancelAnimationFrame: 'readonly',
        AbortController: 'readonly',
        Notification: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        FileReader: 'readonly',
        AudioContext: 'readonly',
        globalThis: 'readonly',
        self: 'readonly',
        caches: 'readonly',
        process: 'readonly'
      }
    },
    linterOptions: {
      reportUnusedDisableDirectives: true
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'no-undef': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      eqeqeq: ['error', 'smart'],
      'no-implicit-globals': 'error',
      curly: ['error', 'multi-line'],
      'max-len': ['warn', { code: 120, ignoreUrls: true, ignoreStrings: true }]
    }
  }
];
