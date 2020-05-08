class LineBarChart {

  constructor(context, lineTitle, barTitle) {
    this.animationDuration = 50;
    this.barTitle = barTitle;
    this.context = context;
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
      borderColor: "#FF1111",
      data: this.lineData,
      fill: false,
      label: this.lineTitle,
      type: "line",
      yAxisID: 1,
    };
  }

  barDataset() {
    return {
      borderColor: "#FF0000",
      data: this.barData,
      fill: false,
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
      "Novos casos no dia"
    );
    caseDailyChart.setData(
      data.daily.date,
      data.daily.confirmed,
      data.daily.new_confirmed
    );
    caseDailyChart.draw();

    deathDailyChart = new LineBarChart(
      jQuery("#death-daily-chart")[0].getContext("2d"),
      "Óbitos confirmados acumulados",
      "Novos óbitos no dia"
    );
    deathDailyChart.setData(
      data.daily.date,
      data.daily.deaths,
      data.daily.new_deaths
    );
    deathDailyChart.draw();

    caseWeeklyChart = new LineBarChart(
      jQuery("#case-weekly-chart")[0].getContext("2d"),
      "Casos confirmados acumulados",
      "Novos casos na semana"
    );
    caseWeeklyChart.setData(
      data.weekly.epidemiological_week,
      data.weekly.confirmed,
      data.weekly.new_confirmed
    );
    caseWeeklyChart.draw();

    deathWeeklyChart = new LineBarChart(
      jQuery("#death-weekly-chart")[0].getContext("2d"),
      "Óbitos confirmados acumulados",
      "Novos óbitos na semana"
    );
    deathWeeklyChart.setData(
      data.weekly.epidemiological_week,
      data.weekly.deaths,
      data.weekly.new_deaths
    );
    deathWeeklyChart.draw();
  });
});
