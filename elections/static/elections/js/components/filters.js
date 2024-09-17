import { normalize } from "./utils/normalize.js"

export const filters = {
  delimiters: ["[[", "]]"],
  components: {
    "n-auto-complete": naive.NAutoComplete,
    "n-button": naive.NButton,
    "n-date-picker": naive.NDatePicker,
    "n-form": naive.NForm,
    "n-form-item": naive.NFormItem,
    "n-input": naive.NInput,
    "n-radio": naive.NRadio,
    "n-radio-group": naive.NRadioGroup,
    "n-select": naive.NSelect,
  },
  props: {
    context: { type: Object },
    handleSearch: { type: Function },
    party: { type: String },
    role: { type: String },
    search: { type: String },
    state: { type: String },
    type: { type: String },
    year: { type: String },
  },
  setup(props, { emit }) {
    const formatToSelect = (option) => option.map(opt => ({ label: opt, value: opt }))
    const party = Vue.computed({
      get() { return props.party },
      set(value) { emit("update:party", value) },
    })
    const role = Vue.computed({
      get() { return props.role },
      set(value) { emit("update:role", value) },
    })
    const search = Vue.computed({
      get() { return props.search },
      set(value) { emit("update:search", value) },
    })
    const state = Vue.computed({
      get() { return props.state },
      set(value) { emit("update:state", value) },
    })
    const type = Vue.computed({
      get() { return props.type },
      set(value) { emit("update:type", value) },
    })

    const getCurrentSelectedCity = () => {
      if (!search.value) {
        return
      }
      const splitedValue = search.value.split("-")
      splitedValue.pop()
      const currentCity = splitedValue.join(" ")
      return currentCity
    }

    const searchCity = Vue.ref(getCurrentSelectedCity())
    const cityOptions = Vue.ref(props.context.data.metadata.municipios)
    const handleSearchCityKeyUp = async (keydown) => {
      if (keydown.key === "Enter" && typeof value === "string" && value.length === 0) {
        await handleSelectCity(searchCity.value)
      }
    }
    const handleSelectCity = async (value) => {
      if (typeof value === "string" && value.length === 0) {
        search.value = ``
        await props.handleSearch()
        return
      }
      const valueSplited = value.split("-")
      const valueState = valueSplited.pop()
      const valueCity = valueSplited.join(" ")
      const valueCityNormalized = normalize(valueCity).replace(/\s+/g, "-").toLowerCase() + "-" + valueState
      const result = props.context.data.metadata.municipios.find(mun => mun.value === valueCityNormalized)
      search.value = `${result.label}-${result.estado}`
      await props.handleSearch()
    }
    const handleSearchCity = (value) => {
      searchCity.value = value
      // Reset cityOptions values
      if (state.value && state.value !== "Todos") {
        cityOptions.value = props.context.data.metadata.municipios.filter(mun => mun.estado === state.value)
      } else {
        cityOptions.value = props.context.data.metadata.municipios
      }

      // Filter searched value
      cityOptions.value = cityOptions.value.filter(mun =>
        normalize(mun.label)
          .trim()
          .toLowerCase()
          .includes(
            normalize(value).trim().toLowerCase()
          )
      )
    }
    const handleSearchCityBlur = async () => {
      const citiesSelected = cityOptions.value.filter(city => city.label === searchCity.value)
      if (!citiesSelected.length || citiesSelected.length > 1) {
        searchCity.value = ""
        await handleSelectCity(searchCity.value)
      } else if (citiesSelected.length === 1) {
        const citySelected = citiesSelected[0]
        await handleSelectCity(citySelected.label + "-" + citySelected.estado)
      }
    }
    const handleSearchRadioUpdate = (value) => {
      type.value = value
      // Clear searchCity and search values every radio value change
      searchCity.value = ""
      search.value = ""
    }
    const handleSelectState = (value) => {
      state.value = value
      searchCity.value = ""
      search.value = ""
    }
    return {
      cityOptions,
      formatToSelect,
      handleSearchCity,
      handleSearchCityBlur,
      handleSearchCityKeyUp,
      handleSearchRadioUpdate,
      handleSelectCity,
      handleSelectState,
      labelStyle: {
        fontSize: '10px',
        flexDirection: 'column-reverse',
        fontWeight: '500',
      },
      options: props.context.data.metadata[2024],
      party,
      renderLabel: (option) => {
        return [
          option.label,
          ' ',
          Vue.h(
            naive.NTag,
            { size: 'small', type: 'info' },
            { default: () => option.estado }
          )
        ]
      },
      role,
      search,
      searchCity,
      state,
      type,
      types: [
        {
          value: 'cidade',
          label: 'CIDADE'
        },
        {
          value: 'nome',
          label: 'CANDIDATO'
        },
      ].map((s) => {
        s.value = s.value.toLowerCase()
        return s
      })
    }
  },
  template: `
    <n-form
      class="d-flex flex-column flex-xl-row align-items-xl-center justify-content-center gap-3 mx-lg-auto border-bottom border-primary bg-election-secondary w-full px-4 px-xl-2 p-b-xl-0 pb-2 pt-3"
    >
      <n-form-item label="ANO" :label-style>
        <n-select
          value="2024"
          filterable
          :options="formatToSelect([2024])"
          style="width: 102px"
          clearable
          disabled
        />
      </n-form-item>
      <n-form-item label="CARGO" :label-style>
        <n-select
          v-model:value="role"
          filterable
          placeholder="Selecione Cargo"
          :options="formatToSelect(options.cargo)"
          style="width: 150px"
        />
      </n-form-item>
      <n-form-item label="ESTADO" :label-style>
        <n-select
          v-model:value="state"
          filterable
          placeholder="Selecione Estado"
          :options="options.estado"
          style="width: 150px"
          :on-update:value="handleSelectState"
        />
      </n-form-item>
      <n-form-item label="PARTIDO" :label-style>
        <n-select
          v-model:value="party"
          filterable
          placeholder="Selecione Partido"
          :options="formatToSelect(options.partido)"
          style="width: 150px"
        />
      </n-form-item>
      <n-form-item>
        <div class="d-flex flex-column" style="margin-top: -24.5px">
          <div>
            <span class="me-2" :style="labelStyle">PESQUISA</span>
            <n-radio-group
              v-model:value="type"
              name="radiogroup"
              :size="'small'"
              :on-update:value="handleSearchRadioUpdate"
            >
              <n-radio
                v-for="item in types"
                :key="item.value"
                :value="item.value"
                :label="item.label"
                style="font-size: 10px; --n-label-font-weight: 500; --n-label-padding: 0 8px 0 4px"
              ></n-radio>
            </n-radio-group>
          </div>
          <n-input
            v-if="!type || type === 'nome'"
            v-model:value="search"
            @keyup="handleSearch"
            style="width: 250px"
            placeholder="Pesquisa"
            @change="handleSearch"
          />
          <n-auto-complete
            v-else
            v-model:value="searchCity"
            :options="cityOptions"
            placeholder="Digite nome de cidade"
            :render-label="renderLabel"
            :input-props="{ onKeydown: handleSearchCityKeyUp }"
            :on-blur="handleSearchCityBlur"
            :on-select="handleSelectCity"
            :on-update:value="handleSearchCity"
            style="width: 250px"
          />
        </div>
      </n-form-item>
      <n-button type="primary" style="padding: 0 12px" @click="handleSearch">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          fill="currentColor"
          class="bi bi-search"
          viewBox="0 0 16 16"
        >
          <path
            d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"
          />
        </svg>
      </n-button>
    </n-form>
  `
}
