import js from '@eslint/js';
import globals from 'globals';
import pluginVue from 'eslint-plugin-vue';
import { defineConfig } from 'eslint/config';


export default defineConfig([
    {
        files: ['**/*.{js,mjs,cjs,vue}'],
        plugins: {js},
        extends: ['js/recommended'],
    },
    {
        files: ['**/*.{js,mjs,cjs,vue}'],
        languageOptions: {
            globals: globals.browser
        }
    },
    pluginVue.configs['flat/recommended'],
    {
        rules: {
            'vue/first-attribute-linebreak': 'off',
            'vue/html-closing-bracket-newline': 'off',
            'vue/html-indent': ['warn', 4, {baseIndent: 0}],
            'vue/html-self-closing': 'off',
            'vue/max-attributes-per-line': 'off',
            'vue/multi-word-component-names': 'off',
            'vue/script-indent': ['warn', 4, {baseIndent: 0}],
            'vue/singleline-html-element-content-newline': 'off',
        }
    },
]);
