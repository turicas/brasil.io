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
    "n-gi": naive.NGi,
    "n-grid": naive.NGrid,
    "n-h1": naive.NH1,
    "n-pagination": naive.NPagination,
    "n-space": naive.NSpace,
    "n-tag": naive.NTag,
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
    const state = Vue.ref(filters.estado)
    const type = Vue.ref(filters.t)
    const year = Vue.ref(filters.ano)
    const title = Vue.ref(props.context.data.title)
    const pageReactive = Vue.reactive({
      page: Number(props.context.data.number),
      pageCount: Number(props.context.data.num_pages),
      pageSize: Number(props.context.data.page_size),
      pageSizes: [10, 20, 40, 100],
      showSizePicker: true,
      pageSlot: 5
    })

    Vue.onMounted(async () => {
      data.value = props.context.data.items
      loading.value = false
    });

    const columns = [
      {
        title: "Nome",
        key: "name",
        sorter: true,
        minWidth: "250px"
      },
      {
        title: "Path",
        key: "path",
        sorter: true,
        minWidth: "60px"
      },
      {
        title: "Ano",
        key: "year",
        sorter: true,
        minWidth: "400px"
      }
    ]

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

      if (pageReactive.pageSize && pageReactive.pageSize !== 10) {
        defaultRequests["page_size"] = pageReactive.pageSize
      } else if (request.page_size) {
        delete request.page_size
      }

      if (sort.value) { defaultRequests["sort"] = sort.value }
      if (order.value) { defaultRequests["order"] = order.value }

      loading.value = true

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
        const pageSize = query.page_size ? Number(query.page_size) : 10
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
      columns,
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
    <div class="container pt-5">
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
      <n-h1>[[ title ]]</n-h1>
      <div class="mb-5 mt-4">
        <n-grid :x-gap="12" :y-gap="12" cols="1 640:2 1024:4">
          <template v-for="item in data">
            <n-gi>
              <n-card hoverable style="margin: auto;">
                <div class="text-center" style="transform: rotate(0);">
                  <n-avatar
                    round
                    :size="48"
                    src="empty.png"
                    fallback-src="/static/elections/img/politics/default-avatar.jpg"
                  />
                  <h2 class="fs-5 mb-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-box" viewBox="0 0 16 16">
                      <path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5 8 5.961 14.154 3.5zM15 4.239l-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.239v7.923zM7.443.184a1.5 1.5 0 0 1 1.114 0l7.129 2.852A.5.5 0 0 1 16 3.5v8.662a1 1 0 0 1-.629.928l-7.185 2.874a.5.5 0 0 1-.372 0L.63 13.09a1 1 0 0 1-.63-.928V3.5a.5.5 0 0 1 .314-.464z"/>
                    </svg>
                    Partido <strong>00 00 0</strong></h2>
                  <div class="d-flex flex-column gap-1 small">
                    <a href="#" class="text-decoration-none" style="height: 40px">[[ item.name ]]</a>
                  </div>
                  <div>
                    <n-tag size="small" round>
                      indeferido
                    </n-tag>
                  </div>
                  <a :href="'/elections' + item.path" class="stretched-link"></a>
                </div>
              </n-card>
            </n-gi>
          </template>
        </n-grid>
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
