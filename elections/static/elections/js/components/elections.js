import { getContext } from "./utils/getContext.js"
import { electionGallery } from "./electionGallery.js"

const App = {
  delimiters: ["[[", "]]"],
  components: {
    "n-config-provider": naive.NConfigProvider,
    "election-gallery": electionGallery,
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
        primaryColor: "rgb(64, 68, 147)",
        primaryColorHover: "rgb(54, 58, 137)"
      },
      Card: {
        color: "#eef0ff"
      }
    }

    const darkThemeOverrides = {
      common: {
        primaryColor: "rgb(94, 98, 177)",
        primaryColorHover: "rgb(84, 88, 167)"
      },
      Button: {
        textColorPrimary: "#FFF",
        textColorHoverPrimary: "#FFF",
        textColorPressedPrimary: "#FFF",
        textColorFocusPrimary: "#FFF",
        colorPressedPrimary: "rgb(54, 58, 137)"
      },
      Card: {
        color: "#2c2e39"
      },
      Pagination: {
        itemTextColorHover: "rgb(184, 188, 247)",
        itemTextColorPressed: "rgb(184, 188, 247)",
        itemTextColorActive: "rgb(184, 188, 247)"
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
        <election-gallery :context />
      </n-config-provider>
    </div>
  `,
}

const r = VueRouter.createRouter({
  history: VueRouter.createWebHistory(),
  routes: [{ path: window.location.pathname, component: App, name: 'home' }],
})

Vue.createApp(App).use(r).mount("#app")
