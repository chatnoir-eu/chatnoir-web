import Vue from 'vue'
import ChatNoirApp from './ChatNoir.vue'
import './assets/css/index.min.css'

Vue.config.productionTip = true

new Vue({
    render: h => h(ChatNoirApp),
}).$mount('#app')
