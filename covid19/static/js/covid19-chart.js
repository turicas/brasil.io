var caseDailyTotalChart, caseDailyNewChart, deathDailyTotalChart, deathDailyNewChart;

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
      title: {
        display: true,
        text: options.title,
      },
      animation: {duration: this.animationDuration},
      bezierCurve: false,
      scales: {
        yAxes: this.yAxes(),
      },
    };
  }

  yAxes() {
    var data = [
      {
        id: 1,
        position: "left",
        scaleLabel: {
          labelString: this.title,
          display: true,
        },
        stacked: false,
        ticks: {
          beginAtZero: true,
        },
        type: "linear",
      },
    ];
    if (this.options.minY !== undefined) {
      data[0].ticks.beginAtZero = false;
      data[0].ticks.min = this.options.minY;
    }
    return data;
  }

  datasets() {
    var result = new Array();
    for (var index = 0; index < this.yLabels.length; index++) {
      result.push({
        borderColor: this.colors[index],
        data: this.yData[index],
        fill: false,
        label: this.yLabels[index],
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
        label: this.yLabels[index],
        type: this.chartType(),
        yAxisID: 1,
      });
    }
    return result;
  }

}

jQuery(document).ready(function(){
  var deathsCompareTitle, deathsTitle, graphSource;
  if (placeType() == "country") {
    deathsTitle = "Causas de óbitos por semana epidemiológica (Brasil)";
    deathsCompareTitle = "Óbitos novos por semana epidemiológica 2019 vs 2020 (Brasil)";
    graphSource = "Fonte: Secretarias Estaduais de Saúde/Consolidação por Brasil.IO";
  }
  else if (placeType() == "state" || placeType() == "city") {
    deathsTitle = `Causas de óbitos por semana epidemiológica (${selectedStateAcronym})`;
    deathsCompareTitle = `Óbitos novos por semana epidemiológica 2019 vs 2020 (${selectedStateAcronym})`;
    graphSource = `Fonte: SES-${selectedStateAcronym}/Consolidação por Brasil.IO`;
  }
  var deathsSource = 'Fonte: <a href="https://transparencia.registrocivil.org.br/registral-covid">Registro Civil</a>. *Nota: as últimas 2 semanas não estão representadas pois os dados estão em processamento pelos cartórios.';

  graphSource += ". *Nota: dados sendo consolidados para os últimos dias.";
  jQuery.getJSON(dataURL.historicalDaily, function (data) {
    caseDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.confirmed.color],
      divId: "case-daily-chart-1",
      title: "Casos confirmados acumulados por dia",
      xData: data.from_states.date,
      yLabels: ["Casos confirmados"],
      yData: [data.from_states.confirmed],
      source: graphSource,
    }).draw();
    caseDailyNewChart = new MultiBarChart({
      colors: [hexToRGBA(dataConfig.confirmed.color, 0.5)],
      divId: "case-daily-chart-2",
      title: "Novos casos confirmados por dia",
      xData: data.from_states.date,
      yLabels: ["Casos confirmados"],
      yData: [data.from_states.new_confirmed],
      source: graphSource,
    }).draw();
    deathDailyTotalChart = new MultiLineChart({
      colors: [dataConfig.deaths.color],
      divId: "death-daily-chart-1",
      title: "Óbitos confirmados acumulados por dia",
      xData: data.from_states.date,
      yLabels: ["Óbitos confirmados"],
      yData: [data.from_states.deaths],
      source: graphSource,
    }).draw();
    deathDailyNewChart = new MultiBarChart({
      colors: [hexToRGBA(dataConfig.deaths.color, 0.5)],
      divId: "death-daily-chart-2",
      title: "Novos óbitos confirmados por dia",
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
      title: deathsTitle,
      source: deathsSource,
      xData: data.from_registries.epidemiological_week,
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
      colors: ["#0000FF", "#FF0000"],
      divId: "death-weekly-years-chart",
      title: deathsCompareTitle,
      source: deathsSource,
      xData: data.from_registries.epidemiological_week,
      yLabels: [
        "Óbitos na semana 2019",
        "Óbitos na semana 2020",
      ],
      yData: [
        data.from_registries.new_deaths_total_2019,
        data.from_registries.new_deaths_total,
      ],
      minY: 5000,
    }).draw();
  });
});
