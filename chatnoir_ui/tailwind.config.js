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
                DEFAULT: '#D34927',
                '50': '#F3C9BE',
                '100': '#F0BAAD',
                '200': '#EA9E8B',
                '300': '#E38168',
                '400': '#DD6446',
                '500': '#D34927',
                '600': '#BE4223',
                '700': '#A83A1F',
                '800': '#93331B',
                '900': '#7D2B17'
            },
            gray: {
                DEFAULT: '#A8A4A3',
                '50': '#FFFFFF',
                '100': '#F8F7F7',
                '200': '#E4E2E2',
                '300': '#D0CECD',
                '400': '#BCB9B8',
                '500': '#A8A4A3',
                '600': '#908A89',
                '700': '#76716F',
                '800': '#5C5857',
                '900': '#423F3E'
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
