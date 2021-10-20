module.exports = {
    purge: [
        './src/**/*.html',
        './src/**/*.vue',
    ],
    darkMode: 'class',
    theme: {
        colors: {
            transparent: 'transparent',
            current: 'currentColor',
            black: '#000',
            white: '#fff',
            red: {
                50: '#fdfcf9',
                100: '#fbf1e4',
                200: '#f7d4c7',
                300: '#eba899',
                400: '#e4796a',
                500: '#d35547',
                600: '#b93b2f',
                700: '#912c24',
                800: '#661e19',
                900: '#3f130f',
            },
            gray: {
                50: '#fafafa',
                100: '#f4f4f5',
                200: '#e4e4e7',
                300: '#d4d4d8',
                400: '#a1a1aa',
                500: '#71717a',
                600: '#52525b',
                700: '#3f3f46',
                800: '#27272a',
                900: '#18181b',
            },
        },
        fill: theme => theme('colors'),
        shadows: {
            red: '0 2px 4px 0 rgba(288, 121, 106, 0.10)'
        },
    },
    variants: {
        extend: {},
    },
    plugins: [],
}
