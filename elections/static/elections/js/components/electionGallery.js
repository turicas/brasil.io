import { api } from "./utils/api.js"
import { filters } from "./filters.js"

export const electionGallery = {
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
    "n-empty": naive.NEmpty,
    "n-gi": naive.NGi,
    "n-grid": naive.NGrid,
    "n-pagination": naive.NPagination,
    "n-space": naive.NSpace,
    "n-spin": naive.NSpin,
    filters,
  },
  setup(props) {
    const data = Vue.ref([])
    const loading = Vue.ref(true)
    const order = Vue.ref(null)
    const sort = Vue.ref(null)
    const filters = props.context.data.filters
    const party = Vue.ref(filters.partido)
    const role = Vue.ref(filters.cargo)
    const search = Vue.ref(filters.q ? filters.q : '')
    const state = Vue.ref(filters.uf)
    const type = Vue.ref(filters.t)
    const year = Vue.ref(filters.ano)
    const title = Vue.ref(props.context.data.title)
    const pageReactive = Vue.reactive({
      page: Number(props.context.data.number),
      pageCount: Number(props.context.data.num_pages),
      pageSize: Number(props.context.data.page_size),
      pageSizes: [40, 80, 120],
      showSizePicker: true,
      pageSlot: 5
    })

    Vue.onMounted(async () => {
      data.value = props.context.data.items
      loading.value = false
    });

    const route = VueRouter.useRoute()
    const router = VueRouter.useRouter()

    const updateUrl = (query) => {
      router.push({ query })
    }

    const handlePageChange = async (currentPage) => {
      await requestApi({ page: currentPage })
      pageReactive.page = currentPage
      // Scroll top
      window.scroll({ top: 0})
    }

    const handleSorterChange = async (sorter) => {
      if (!sorter.order) {
        sort.value = null
        order.value = null
        await requestApi()
        return
      }
      sort.value = sorter.columnKey
      order.value = sorter.order === "ascend" ? "asc" : "desc"
      await requestApi()
    }

    const handlePageSizeChange = async (pageSize) => {
      pageReactive.pageSize = pageSize
      pageReactive.page = 1
      await requestApi()
    }

    const requestApi = async (request = {}) => {
      loading.value = true

      const defaultRequests = {}
      if (party.value) { defaultRequests["partido"] = party.value }
      if (role.value) { defaultRequests["cargo"] = role.value }
      if (type.value) { defaultRequests["t"] = type.value }
      if (search.value) { defaultRequests["q"] = search.value }
      if (state.value) { defaultRequests["uf"] = state.value }
      if (year.value) { defaultRequests["ano"] = year.value }
      if (pageReactive.page && pageReactive.page > 1) {
        defaultRequests["page"] = pageReactive.page
      }
      if (request.page && request.page === 1) {
        delete request.page
        delete defaultRequests.page
      }

      if (pageReactive.pageSize && pageReactive.pageSize !== 40) {
        defaultRequests["page_size"] = pageReactive.pageSize
      } else if (request.page_size) {
        delete request.page_size
      }

      if (sort.value) { defaultRequests["sort"] = sort.value }
      if (order.value) { defaultRequests["order"] = order.value }

      const requestFormated = { ...defaultRequests, ...request, format: 'json' }
      const requestResult = await api("", requestFormated)

      updateUrl({ ...defaultRequests, ...request })

      data.value = requestResult.items
      pageReactive.pageCount = requestResult.num_pages
      title.value = requestResult.title

      loading.value = false
    }

    const requestApiSearch = async () => {
      await requestApi()
    }

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
      pageReactive.page = 1
      requestApiSearch()
    })

    let firstLoad = true
    Vue.watch(
      () => route.query,
      async () => {
        if (firstLoad) {
          firstLoad = false
          return
        }

        const query = route.query
        const page = query.page ? Number(query.page) : 1
        const pageSize = query.page_size ? Number(query.page_size) : 40
        const q = query.q ? query.q : ''
        let updated = false

        if (page !== pageReactive.page) {
          pageReactive.page = page
          updated = true
        }
        if (pageSize !== pageReactive.pageSize) {
          pageReactive.pageSize = pageSize
          updated = true
        }
        if (q !== search.value) {
          search.value = q
          updated = true
        }

        if (updated) {
          await requestApi()
        }
      }
    )

    return {
      data,
      handlePageChange,
      handlePageSizeChange,
      handleSearch,
      handleSorterChange,
      loading,
      pagination: pageReactive,
      party,
      role,
      search,
      state,
      title,
      type,
      year,
    }
  },
  template: `
    <div>
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
      <div class="border-bottom border-primary my-5">
        <h2 class="election-text-primary fw-normal">[[ title ]]</h2>
      </div>
      <div class="mb-5">
        <n-spin :show="loading">
          <n-grid v-if="data.length" :x-gap="12" :y-gap="12" cols="1 640:2 1024:4">
            <template v-for="item in data">
              <n-gi>
                <n-card class="election-card" style="margin: auto; transform: rotate(0);">
                  <div>
                    <div class="d-flex gap-3 align-items-center">
                      <n-avatar
                        round
                        :size="80"
                        src="empty.png"
                        fallback-src="/static/elections/img/politics/default-avatar.jpg"
                        class="border border-secondary-subtle"
                      />
                      <div class="d-flex flex-column">
                        <span class="fw-bold">00</span>
                        <span>Partido</span>
                        <span class="election-text-primary text-uppercase">Prefeito em 2024</span>
                      </div>
                    </div>
                    <div class="d-flex flex-column justify-content-center gap-1 small mt-2">
                      <span class="election-text-primary fw-bold text-truncate">[[ item.name ]]</span>
                    </div>
                    <div class="d-flex">
                      <span class="election-text-tertiary text-truncate">Município - ES</span>
                    </div>
                    <a
                      :href="item.path" class="stretched-link bg-primary"
                      :title="item.name.length > 35 ? item.name : ''"
                    ></a>
                  </div>
                </n-card>
              </n-gi>
            </template>
          </n-grid>
          <n-empty
            v-else
            class="d-flex justify-content-center rounded border border-2"
            description="Nada encontrado"
            style="height: 450px;"
          />
        </n-spin>
        <n-space class="pt-5 mx-auto d-flex justify-content-center">
          <n-pagination
            v-model:page="pagination.page"
            show-size-picker
            :page-count="pagination.pageCount"
            :pagination="pagination"
            :page-size="pagination.pageSize"
            :page-sizes="pagination.pageSizes"
            @update:page-size="handlePageSizeChange"
            @update:page="handlePageChange"
            @update:sorter="handleSorterChange"
          />
        </n-space>
      </div>
    </div>
  `,
}
