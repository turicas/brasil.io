$(document).ready(function () {

  $('.table').DataTable(
    {
      language: {
        url: dashVars.dataTablesPtBR
      },
      ajax: {
        url: request,
        dataSrc: "city_data"
      },
      columns: [
        { title: "Data", data: "date", type: "date" },
        { title: "Munincípio", data: "city" },
        { title: "UF", data: "state", visible: state != "None" ? false : true },
        { title: "Confirmados", data: "confirmed" },
        { title: "Confirmado por 100k hab.", data: "confirmed_per_100k_inhabitants" },
        { title: "Óbitos", data: "deaths" },
        { title: "Letalidade", data: "death_rate_percent", },
        { title: "Óbitos por 100k hab.", data: "deaths_per_100k_inhabitants" },
      ],
      "columnDefs": [
        {
          "targets": [6],
          "render": function (data, type, row, meta) {
            return formatter.format(data) + "%";
          }
        },
        {
          "targets": [4, 3, 5, 7],
          "render": function (data, type, row, meta) {
            return data.toLocaleString("pt-BR");
          }
        }
      ]
    }
  );
});