module.exports = {
    extends: [
        'plugin:vue/recommended'
    ],
    rules: {
        'vue/script-indent': ['warn', 4, {baseIndent: 0}],
        'vue/html-indent': ['warn', 4, {baseIndent: 0}],
        'vue/max-attributes-per-line': 'off',
        'vue/html-self-closing': 'off',
        'vue/html-closing-bracket-newline': 'off',
        'vue/singleline-html-element-content-newline': 'off',
        'vue/script-setup-uses-vars': 'off',
        'vue/multi-word-component-names': 'off',
        'vue/first-attribute-linebreak': 'off',
    }
}
