import { createApp } from 'vue'
import ChatNoirApp from './ChatNoir.vue'
import router from './routes'

import './assets/css/index.css'

export default createApp(ChatNoirApp).use(router).mount('#app')
