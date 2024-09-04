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
    "n-space": naive.NSpace,
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
    const search = Vue.computed({
      get() { return props.search },
      set(value) { emit("update:search", value) },
    })
    return {
      search,
      labelStyle: {
        fontSize: '10px',
        flexDirection: 'column-reverse',
        fontWeight: '500',
      },
      types: [
        {
          value: 'cidade',
          label: 'CIDADE'
        },
        {
          value: 'candidato',
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
      class="d-flex flex-column flex-xl-row align-items-xl-center justify-content-center gap-3 mx-lg-auto pt-3 border-bottom border-primary bg-election-secondary w-full px-4 pb-4 px-xl-2 p-b-xl-0"
    >
      <n-form-item label="ANO" :label-style>
        <n-date-picker
          v-model:value="year"
          type="year"
          placeholder="Ano"
          style="width: 102px"
        />
      </n-form-item>
      <n-form-item label="CARGO" :label-style>
        <n-select
          v-model:value="role"
          filterable
          placeholder="Selecione Cargo"
          :options="options"
          style="width: 150px"
        />
      </n-form-item>
      <n-form-item label="ESTADO" :label-style>
        <n-select
          v-model:value="state"
          filterable
          placeholder="Selecione Estado"
          :options="options"
          style="width: 150px"
        />
      </n-form-item>
      <n-form-item label="PARTIDO" :label-style>
        <n-select
          v-model:value="party"
          filterable
          placeholder="Selecione Partido"
          :options="options"
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
          ></n-input>
        </div>
      </n-form-item>
      <n-button type="primary">
        Pesquisar
      </n-button>
    </n-form>
  `
}
