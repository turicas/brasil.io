export const filters = {
  delimiters: ["[[", "]]"],
  components: {
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
    return {
      formatToSelect,
      labelStyle: {
        fontSize: '10px',
        flexDirection: 'column-reverse',
        fontWeight: '500',
      },
      options: props.context.data.metadata[2024],
      party,
      role,
      search,
      state,
      type,
      types: [
        {
          value: 'cidade',
          label: 'CIDADE'
        },
        {
          value: 'name',
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
          :options="formatToSelect(options.estado)"
          style="width: 150px"
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
            <n-radio-group v-model:value="type" name="radiogroup" :size="'small'">
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
            v-model:value="search"
            @keyup="handleSearch"
            style="width: 250px"
            placeholder="Pesquisa"
            clearable
            @change="handleSearch"
          ></n-input>
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
