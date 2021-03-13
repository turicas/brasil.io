var caseDailyNewChart,
  caseDailyTotalChart,
  deathDailyNewChart,
  deathDailyTotalChart,
  deathWeeklyChart,
  deathWeeklyCompareChart,
  deathWeeklyExcessChart,
  excessDeathsWeeklyChart;


jQuery(document).ready(function(){
  var graphSource, titleAppend;
  if (placeType() == "country") {
    graphSource = "Fonte: Secretarias Estaduais de Saúde/Consolidação por Brasil.IO";
    titleAppend = " (Brasil)";
  }
  else if (placeType() == "state" || placeType() == "city") {
    graphSource = `Fonte: SES-${selectedStateAcronym}/Consolidação por Brasil.IO`;
    titleAppend = ` (${selectedStateAcronym})`;
  }
  var deathsTitle = `Causas de óbitos por semana epidemiológica${titleAppend}`;
  var deathsCompareTitle = `Óbitos novos por semana epidemiológica 2019 vs 2020${titleAppend}`;
  var deathsSourceLink = 'Fonte: <a href="https://transparencia.registrocivil.org.br/registral-covid" title="Ver fonte">Registro Civil</a>.';
  var deathsSourceNote = " *Nota: as últimas 2 semanas não estão representadas pois os dados estão em processamento pelos cartórios.";
  var deathsSource = deathsSourceLink + deathsSourceNote;
  var deathsGroupSource = deathsSourceLink + " Grupos: COVID-19 (suspeita ou confirmação por COVID-19), Outras respiratórias (pneumonia + insuf. resp. + SRAG), Outras (septicemia + indeterminada + outras causas naturais não externas). Dados de 2021 ainda sendo consolidados." + deathsSourceNote;
  var deathsExcessSource = deathsSourceLink + " Excesso por semana = novos óbitos totais na semana em 2020 - novos óbitos totais na semana em 2019. Dados de 2021 ainda sendo consolidados." + deathsSourceNote;

  graphSource += ". *Nota: dados sendo consolidados para os últimos dias.";
  jQuery.getJSON(dataURL.historicalDaily, function (data) {
    caseDailyNewChart = new MultiBarLineChart({
      colors: [hexToRGBA(dataConfig.confirmed.color, 0.5), dataConfig.confirmed.color],
      divId: "case-daily-chart-1",
      title: `Novos casos confirmados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Casos confirmados", "Média móvel 7 dias"],
      yData: [data.from_states.new_confirmed, arrayToInt(movingAverage(data.from_states.new_confirmed, 7))],
      source: graphSource,
    }).draw();
    deathDailyNewChart = new MultiBarLineChart({
      colors: [hexToRGBA(dataConfig.deaths.color, 0.5), dataConfig.deaths.color],
      divId: "death-daily-chart-1",
      title: `Novos óbitos confirmados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Óbitos confirmados", "Média móvel 7 dias"],
      yData: [data.from_states.new_deaths, arrayToInt(movingAverage(data.from_states.new_deaths, 7))],
      source: graphSource,
    }).draw();
    caseDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.confirmed.color],
      divId: "case-daily-chart-2",
      title: `Casos confirmados acumulados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Casos confirmados"],
      yData: [data.from_states.confirmed],
      source: graphSource,
    }).draw();
    deathDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.deaths.color],
      divId: "death-daily-chart-2",
      title: `Óbitos confirmados acumulados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Óbitos confirmados"],
      yData: [data.from_states.deaths],
      source: graphSource,
    }).draw();
  });

  jQuery.getJSON(dataURL.historicalWeekly, function (data) {
    deathWeeklyChart = new MultiLineChart({
      colors: ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#C0C0C0"],
      divId: "death-weekly-2020-chart",
      source: deathsSource,
      title: deathsTitle,
      xData: data.from_registries.epidemiological_week,
      xLabel: "Semana epidemiológica (2020)",
      yLabels: [
        "COVID-19 (confirmada ou suspeita)",
        "Indeterminada",
        "Outras",
        "Pneumonia",
        "Insuf. Respiratória",
        "SRAG",
        "Septicemia",
      ],
      yData: [
        data.from_registries.new_deaths_covid19,
        data.from_registries.new_deaths_indeterminate,
        data.from_registries.new_deaths_others,
        data.from_registries.new_deaths_pneumonia,
        data.from_registries.new_deaths_respiratory_failure,
        data.from_registries.new_deaths_sars,
        data.from_registries.new_deaths_septicemia,
      ],
    }).draw();
    deathWeeklyCompareChart = new MultiLineChart({
      beginAtZero: false,
      colors: ["#0000FF", "#FF0000"],
      divId: "death-weekly-years-chart",
      source: deathsSource,
      title: deathsCompareTitle,
      xData: data.from_registries.epidemiological_week,
      xLabel: "Semana epidemiológica",
      yData: [
        data.from_registries.new_deaths_total_2019,
        data.from_registries.new_deaths_total,
      ],
      yLabels: [
        "Óbitos na semana (2019)",
        "Óbitos na semana (2020)",
      ],
    }).draw();

    deathWeeklyExcessChart = new StackedBarChart({
      colors: [
        [
          "rgba(0,     0, 255, 0.3)",
          "rgba(0,   255,   0, 0.3)",
          "rgba(255,   0,   0, 0.3)",
        ],
        [
          "rgba(0,     0, 255, 1.0)",
          "rgba(0,   255,   0, 1.0)",
          "rgba(255,   0,   0, 1.0)",
        ],
      ],
      divId: "death-weekly-excess-chart-1",
      source: deathsGroupSource,
      stacked: true,
      title: `Novos óbitos (causas agrupadas) por semana epidemiológica${titleAppend}`,
      xData: data.from_registries_excess.epidemiological_week,
      xLabel: "Semana epidemiológica",
      yLabels: [
        [
          "Outras (2019)",
          "Outras respiratórias (2019)",
          undefined,
        ],
        [
          "Outras (2020)",
          "Outras respiratórias (2020)",
          "COVID-19 (2020)",
        ],
      ],
      yData: [
        [
          data.from_registries_excess.new_deathgroup_other_2019,
          data.from_registries_excess.new_deathgroup_other_respiratory_2019,
          data.from_registries_excess.new_deathgroup_covid19_2019,
        ],
        [
          data.from_registries_excess.new_deathgroup_other_2020,
          data.from_registries_excess.new_deathgroup_other_respiratory_2020,
          data.from_registries_excess.new_deathgroup_covid19_2020,
        ],
      ]
    }).draw();
    excessDeathsWeeklyChart = new MultiBarChart({
      colors: [(row) => row.dataset.data[row.dataIndex] >= 0 ? "#FF0000" : "#0000FF" ],
      divId: "death-weekly-excess-chart-2",
      title: `Excesso de novos óbitos por semana epidemiológica${titleAppend}`,
      xData: data.from_registries_excess.epidemiological_week,
      yLabels: ["Óbitos em excesso"],
      yData: [data.from_registries_excess.new_excess_deaths],
      showYLabels: false,
      source: deathsExcessSource,
    }).draw();

  });
});
