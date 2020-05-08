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

class LineBarChart {

  constructor(context, lineTitle, lineColor, barTitle, barColor) {
    this.animationDuration = 50;
    this.barColor = barColor;
    this.barTitle = barTitle;
    this.context = context;
    this.lineColor = lineColor;
    this.lineTitle = lineTitle;
    this.options = {
      animation: {duration: this.animationDuration},
      bezierCurve: false,
      scales: {
        yAxes: [
          {id: 1, labelString: this.lineTitle, stacked: false, beginAtZero: true, position: "left", type: "linear"},
          {id: 2, labelString: this.barTitle, stacked: false, beginAtZero: true, position: "right", type: "linear"},
        ],
      },
    };
  }

  setData(xLabels, lineData, barData) {
    this.xLabels = xLabels;
    this.lineData = lineData;
    this.barData = barData;
  }

  lineDataset() {
    return {
      borderColor: this.lineColor,
      data: this.lineData,
      fill: false,
      label: this.lineTitle,
      type: "line",
      yAxisID: 1,
    };
  }

  barDataset() {
    return {
      backgroundColor: this.barColor,
      data: this.barData,
      label: this.barTitle,
      type: "bar",
      yAxisID: 2,
    };
  }

  draw() {
    this.chart = new Chart(this.context, {
      data: {
        datasets: [
          this.lineDataset(),
          this.barDataset(),
        ],
        labels: this.xLabels,
      },
      options: this.options,
      type: "bar",
    });
  }
}

var caseChart, deathChart;

jQuery(document).ready(function(){
  jQuery.getJSON(dataURL.historicalData, function (data) {
    caseDailyChart = new LineBarChart(
      jQuery("#case-daily-chart")[0].getContext("2d"),
      "Casos confirmados acumulados",
      dataConfig.confirmed.color,
      "Novos casos no dia",
      hexToRGBA(dataConfig.confirmed.color, 0.5),
    );
    caseDailyChart.setData(
      data.from_states.daily.date,
      data.from_states.daily.confirmed,
      data.from_states.daily.new_confirmed
    );
    caseDailyChart.draw();

    deathDailyChart = new LineBarChart(
      jQuery("#death-daily-chart")[0].getContext("2d"),
      "Óbitos confirmados acumulados",
      dataConfig.deaths.color,
      "Novos óbitos no dia",
      hexToRGBA(dataConfig.deaths.color, 0.5),
    );
    deathDailyChart.setData(
      data.from_states.daily.date,
      data.from_states.daily.deaths,
      data.from_states.daily.new_deaths
    );
    deathDailyChart.draw();

    caseWeeklyChart = new LineBarChart(
      jQuery("#case-weekly-chart")[0].getContext("2d"),
      "Casos confirmados acumulados",
      dataConfig.confirmed.color,
      "Novos casos na semana",
      hexToRGBA(dataConfig.confirmed.color, 0.5),
    );
    caseWeeklyChart.setData(
      data.from_states.weekly.epidemiological_week,
      data.from_states.weekly.confirmed,
      data.from_states.weekly.new_confirmed
    );
    caseWeeklyChart.draw();

    deathWeeklyChart = new LineBarChart(
      jQuery("#death-weekly-chart")[0].getContext("2d"),
      "Óbitos confirmados acumulados",
      dataConfig.deaths.color,
      "Novos óbitos na semana",
      hexToRGBA(dataConfig.deaths.color, 0.5),
    );
    deathWeeklyChart.setData(
      data.from_states.weekly.epidemiological_week,
      data.from_states.weekly.deaths,
      data.from_states.weekly.new_deaths
    );
    deathWeeklyChart.draw();
  });
});
