import { createApp } from 'vue'
import ChatNoirApp from './ChatNoir.vue'
import router from './routes'

import './assets/css/index.css'

createApp(ChatNoirApp).use(router).mount('#app')
