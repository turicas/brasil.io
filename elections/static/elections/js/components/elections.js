import { getContext } from "./utils/getContext.js"
import { electionTable } from "./electionTable.js"

const App = {
  delimiters: ["[[", "]]"],
  components: {
    "n-config-provider": naive.NConfigProvider,
    "election-table": electionTable,
  },
  setup() {
    const theme = Vue.ref(null)
    const observer = Vue.ref(null)

    Vue.onBeforeMount(() => {
      if (localStorage.theme === 'dark') {
        theme.value = naive.darkTheme
      } else if (localStorage.theme === 'auto') {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
          theme.value = naive.darkTheme
        } else {
          theme.value = null
        }
      } else {
        theme.value = null
      }

      // Function to handle dataset changes
      const onDatasetChange = (mutationsList) => {
        for (const mutation of mutationsList) {
          if (mutation.type === 'attributes' && mutation.attributeName.startsWith('data-')) {
            theme.value = mutation.target.dataset.bsTheme === 'dark' ? naive.darkTheme : null
          }
        }
      }
      // Select the target element
      const targetNode = document.querySelector('html')
      // Create an observer instance linked to the callback function
      observer.value = new MutationObserver(onDatasetChange)
      // Start observing the target node for configured mutations
      observer.value.observe(targetNode, { attributes: true })
    })

    Vue.onBeforeUnmount(() => {
      observer.value.disconnect()
    })

    const lightThemeOverrides = {
      common: {
        primaryColor: "#2563eb",
        primaryColorHover: "#1d4ed8"
      }
    }

    const darkThemeOverrides = {
      common: {
        primaryColor: "#38bdf8",
        primaryColorHover: "#93c5fd"
      }
    }
    return {
      context: getContext(),
      lightThemeOverrides,
      darkThemeOverrides,
      theme,
      // n-config-provider setup
      ptBR: naive.ptBR,
    }
  },
  template: `
    <div class="container py-5">
      <n-config-provider
        :locale="ptBR"
        :theme="theme"
        :theme-overrides="theme === null ? lightThemeOverrides : darkThemeOverrides"
      >
        <election-table :context />
      </n-config-provider>
    </div>
  `,
}

const r = VueRouter.createRouter({
  history: VueRouter.createWebHistory(),
  routes: [{ path: window.location.pathname, component: App, name: 'home' }],
})

Vue.createApp(App).use(r).mount("#app")
