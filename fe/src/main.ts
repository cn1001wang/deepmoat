import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import ElementPlus from 'element-plus'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './style.scss'
import 'element-plus/dist/index.css'
import 'uno.css'

// ⭐ 关键：必须注册（否则直接报 272）
ModuleRegistry.registerModules([AllCommunityModule])

createApp(App)
  .use(ElementPlus)
  .use(router)
  .mount('#app')
