import { createApp } from 'vue'
import InlineSvg from 'vue-inline-svg'
import ChatNoirApp from '@/ChatNoir.vue'
import router from '@/routes'

import './assets/css/index.css'

const app = createApp(ChatNoirApp).use(router)

// Fix global components not being recognized by JetBrains IDEs.
// See: https://youtrack.jetbrains.com/issue/WEB-48239
const Vue = app
Vue.component('InlineSvg', InlineSvg).mount('#app')

export default Vue
