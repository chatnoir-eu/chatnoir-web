import { createWebHistory, createRouter } from "vue-router"

export default createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'IndexSearch',
            component: () => import('./views/IndexSearch.vue')
        }
    ]
})
