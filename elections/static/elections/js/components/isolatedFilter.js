import { formatedParamsToQueryStrings } from "./utils/api.js"
import { filters } from "./filters.js"

export const isolatedFilter = {
  delimiters: ["[[", "]]"],
  props: {
    context: {
      type: Object
    }
  },
  components: {
    "n-avatar": naive.NAvatar,
    "n-button": naive.NButton,
    "n-card": naive.NCard,
    "n-gi": naive.NGi,
    "n-grid": naive.NGrid,
    "n-h1": naive.NH1,
    "n-pagination": naive.NPagination,
    "n-space": naive.NSpace,
    "n-tag": naive.NTag,
    filters,
  },
  setup() {
    const party = Vue.ref("Todos")
    const role = Vue.ref("Todos")
    const search = Vue.ref(null)
    const state = Vue.ref("Todos")
    const type = Vue.ref("cidade")
    const year = Vue.ref(null)

    const createDebounce = () => {
      let timer
      return(fn, wait = 500) => {
        if (timer) clearTimeout(timer)
        timer = setTimeout(() => {
          if (typeof fn === 'function') {
            fn()
          }
        }, wait)
      }
    }
    const debounce = createDebounce()
    const handleSearch = () => debounce(() => {
      redirectToElectionGallery()
    })

    const redirectToElectionGallery = async (request = {}) => {
      const defaultRequests = {}
      if (party.value) { defaultRequests["partido"] = party.value }
      if (role.value) { defaultRequests["cargo"] = role.value }
      if (type.value) { defaultRequests["t"] = type.value }
      if (search.value) { defaultRequests["q"] = search.value }
      if (state.value) { defaultRequests["uf"] = state.value }
      if (year.value) { defaultRequests["ano"] = year.value }

      const requestFormated = { ...defaultRequests, ...request }

      // Redirect to a new URL
      const location = window.location

      location.href =
        location.protocol +
        "//" +
        location.host +
        "/eleicoes/2024/" +
        formatedParamsToQueryStrings(requestFormated)
    }

    return {
      party,
      role,
      search,
      state,
      type,
      year,
      filters,
      handleSearch
    }
  },
  template: `
    <filters
      :context
      :handleSearch
      v-model:search="search"
      v-model:party="party"
      v-model:role="role"
      v-model:state="state"
      v-model:type="type"
      v-model:year="year"
    />
  `,
}




