var caseDailyNewChart,
  caseDailyTotalChart,
  deathDailyNewChart,
  deathDailyTotalChart,
  deathWeeklyChart,
  deathWeeklyCompareChart,
  deathWeeklyExcessChart,
  excessDeathsWeeklyChart;

function hexToRGBA(hex, rgba) {
  parts = hex.split("");
  parts.shift();
  if (parts.length == 3) {
    parts = [parts[0], parts[0], parts[1], parts[1], parts[2], parts[2]];
  }
  hexNumber = `0x${parts.join("")}`;
  red = (hexNumber >> 16) & 255;
  green = (hexNumber >> 8) & 255;
  blue = hexNumber & 255;
  return `rgba(${red}, ${green}, ${blue}, ${rgba})`;
}

class MultiLineChart {

  chartType() {
    return "line";
  }

  constructor(options) {
    this.animationDuration = options.animationDuration || 0;
    this.colors = options.colors;
    this.canvasElement = document.getElementById(options.divId)
    this.context = this.canvasElement.getContext("2d");
    this.options = options;
    this.title = options.title;
    this.xData = options.xData;
    this.yLabels = options.yLabels;
    this.yData = options.yData;
    this.chartOptions = {
      animation: {duration: this.animationDuration},
      bezierCurve: false,
      legend: {
        display: this.options.showYLabels === undefined ? true : this.options.showYLabels,
        labels: {
          filter: function (legendItem, data) { return legendItem.text !== undefined; },
        },
      },
      scales: {
        yAxes: this.yAxes(),
        xAxes: this.xAxes(),
      },
      title: {
        display: true,
        text: options.title,
      },
    };
  }

  getYLabel(index) {
    return this.yLabels[index];
  }

  xAxes() {
    var axes = [{
      stacked: this.options.stacked === undefined ? false : this.options.stacked,
    }];
    if (this.options.xLabel !== undefined) {
      axes[0].scaleLabel = {
        labelString: this.options.xLabel,
        display: true,
      };
    }
    return axes;
  }

  yAxes() {
    return [
      {
        id: 1,
        position: "left",
        stacked: this.options.stacked === undefined ? false : this.options.stacked,
        ticks: {
          beginAtZero: this.options.beginAtZero === undefined ? true : this.options.beginAtZero,
        },
        type: "linear",
      },
    ];
  }

  datasets() {
    var result = new Array();
    for (var index = 0; index < this.yLabels.length; index++) {
      result.push({
        borderColor: this.colors[index],
        data: this.yData[index],
        fill: false,
        label: this.getYLabel(index),
        type: this.chartType(),
        yAxisID: 1,
      });
    }
    return result;
  }

  draw() {
    this.chart = new Chart(this.context, {
      data: {
        datasets: this.datasets(),
        labels: this.xData,
      },
      options: this.chartOptions,
      type: this.chartType(),
    });
    if (this.options.source !== undefined) {
      var newNode = document.createElement("p");
      newNode.innerHTML = this.options.source;
      this.canvasElement.parentNode.appendChild(newNode);
    }
    return this;
  }
}

class MultiBarChart extends MultiLineChart {

  chartType() {
    return "bar";
  }

  datasets() {
    var result = new Array();
    for (var index = 0; index < this.yLabels.length; index++) {
      result.push({
        backgroundColor: this.colors[index],
        data: this.yData[index],
        label: this.getYLabel(index),
        type: this.chartType(),
        yAxisID: 1,
      });
    }
    return result;
  }

}

class StackedBarChart extends MultiBarChart {

  datasets() {
    var result = new Array();
    for (var stackIndex = 0; stackIndex < this.yData.length; stackIndex++) {
      for (var index = 0; index < this.yData[stackIndex].length; index++) {
        result.push({
          backgroundColor: this.colors[stackIndex][index],
          data: this.yData[stackIndex][index],
          label: this.yLabels[stackIndex][index],
          stack: stackIndex,
          type: this.chartType(),
          yAxisID: 1,
        });
      }
    }
    return result;
  }

}

function startCovid19Chart() {
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
  var deathsSourceLink = 'Fonte: <a href="https://transparencia.registrocivil.org.br/registral-covid">Registro Civil</a>.';
  var deathsSourceNote = " *Nota: as últimas 2 semanas não estão representadas pois os dados estão em processamento pelos cartórios.";
  var deathsSource = deathsSourceLink + deathsSourceNote;
  var deathsGroupSource = deathsSourceLink + " Grupos: COVID-19 (suspeita ou confirmação por COVID-19), Outras respiratórias (pneumonia + insuf. resp. + SRAG), Outras (septicemia + indeterminada + outras causas naturais não externas)." + deathsSourceNote;
  var deathsExcessSource = deathsSourceLink + " Excesso por semana = novos óbitos totais na semana em 2020 - novos óbitos totais na semana em 2019." + deathsSourceNote;
  
  graphSource += ". *Nota: dados sendo consolidados para os últimos dias.";
  
  jQuery.getJSON(dataURL.historicalDaily, function (data) {
    caseDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.confirmed.color],
      divId: "case-daily-chart-1",
      title: `Casos confirmados acumulados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Casos confirmados"],
      yData: [data.from_states.confirmed],
      source: graphSource,
    }).draw();
    caseDailyNewChart = new MultiBarChart({
      colors: [hexToRGBA(dataConfig.confirmed.color, 0.5)],
      divId: "case-daily-chart-2",
      title: `Novos casos confirmados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Casos confirmados"],
      yData: [data.from_states.new_confirmed],
      source: graphSource,
    }).draw();
    deathDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.deaths.color],
      divId: "death-daily-chart-1",
      title: `Óbitos confirmados acumulados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Óbitos confirmados"],
      yData: [data.from_states.deaths],
      source: graphSource,
    }).draw();
    deathDailyNewChart = new MultiBarChart({
      colors: [hexToRGBA(dataConfig.deaths.color, 0.5)],
      divId: "death-daily-chart-2",
      title: `Novos óbitos confirmados por dia${titleAppend}`,
      xData: data.from_states.date,
      yLabels: ["Óbitos confirmados"],
      yData: [data.from_states.new_deaths],
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
}

document.addEventListener("DOMContentLoaded", function () {
  var url = window.location.href.split('/')[3]
  if (url === 'covid19') {
    startCovid19Chart()
  }
});