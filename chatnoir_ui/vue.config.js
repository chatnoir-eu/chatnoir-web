const BundleTracker = require('webpack-bundle-tracker')
const path = require('path');

const DEPLOYMENT_PATH = '/static/'
const DEBUG = process.env.NODE_ENV !== 'production'

module.exports = {
    publicPath: DEBUG ?  'http://localhost:8080/' : DEPLOYMENT_PATH,
    outputDir: path.join(__dirname, 'dist'),

    pages: {
        index: {
            entry: path.join(__dirname, 'src', 'main.js'),
            template: path.join(__dirname, 'src', 'index.html')
        }
    },

    devServer: {
        public: 'localhost:8080',
        headers: {
            'Access-Control-Allow-Origin': '*',
        },
    },

    configureWebpack: {
        plugins: [
            new BundleTracker({
                filename: path.join(__dirname, 'webpack-stats.json')
            }),
        ]
    },
}
