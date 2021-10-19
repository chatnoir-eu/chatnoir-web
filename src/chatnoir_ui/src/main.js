import Vue from 'vue'
import ChatNoirApp from './App.vue'
import './assets/css/index.min.css'

Vue.config.productionTip = false

new Vue({
    render: h => h(ChatNoirApp),
}).$mount('#chatnoir')
