import { api } from "./utils/api.js"
import { filters } from "./filters.js"

export const electionTable = {
  delimiters: ["[[", "]]"],
  props: {
    context: {
      type: Object
    }
  },
  components: {
    "n-data-table": naive.NDataTable,
    "n-input": naive.NInput,
    "n-input-group": naive.NInputGroup,
    "n-button": naive.NButton,
    filters,
  },
  setup(props) {
    const data = Vue.ref([])
    const loading = Vue.ref(true)
    const order = Vue.ref(null)
    const sort = Vue.ref(null)
    const search = Vue.ref(props.context.data.search)
    const pageReactive = Vue.reactive({
      page: Number(props.context.data.number),
      pageCount: Number(props.context.data.num_pages),
      pageSize: 10,
      pageSizes: [10, 20, 30],
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

    const updateUrl = (params) => {
      router.push({ query: params })
    }

    const handlePageChange = async (currentPage) => {
      await requestApi({ page: currentPage })
      pageReactive.page = currentPage
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
      if (search.value) {
        defaultRequests["search"] = search.value
      }
      if (pageReactive.page) {
        defaultRequests["page"] = pageReactive.page
      }

      if (pageReactive.pageSize && pageReactive.pageSize !== 10) {
        defaultRequests["page_size"] = pageReactive.pageSize
      } else if (request.page_size) {
        delete request.page_size
      }

      if (sort.value) {
        defaultRequests["sort"] = sort.value
      }
      if (order.value) {
        defaultRequests["order"] = order.value
      }

      loading.value = true

      const requestFormated = { ...defaultRequests, ...request, format: 'json' }
      const requestResult = await api("", requestFormated)

      updateUrl({ ...defaultRequests, ...request })

      data.value = requestResult.items
      pageReactive.pageCount = requestResult.num_pages

      loading.value = false
    }

    const requestApiSearch = async () => {
      await requestApi()
    }

    const createDebounce = () => {
      let timer
      return(fn, wait = 300) => {
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
        const q = query.search ? query.search : ''
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
      pagination: pageReactive,
      handlePageChange,
      handleSorterChange,
      handlePageSizeChange,
      handleSearch,
      search,
      loading,
    }
  },
  template: `
    <filters :context :handleSearch v-model:search="search" />
    <div class="container py-5">
      <n-data-table
        remote
        :columns="columns"
        :data="data"
        :bordered="false"
        :loading="loading"
        :pagination="pagination"
        :scrollbar-props="{ trigger: 'none', xScrollable: true }"
        @update:page-size="handlePageSizeChange"
        @update:page="handlePageChange"
        @update:sorter="handleSorterChange"
      >
      </n-data-table>
    </div>
  `,
}
