function startCovid19Table() {
  var dt;
  
  if (selectedStateId === undefined) {
    var columns = [
      { width: "18%" },
      { width: "18%" },
      { width: "14%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
    ];
  } else {
    var columns = [
      { width: "25%" },
      { width: "25%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
      { width: "10%" },
    ];
  }

  window.app.dt = jQuery(".mdl-data-table").DataTable({
    autoWidth: false,
    columns: columns,
    scrollY: "600px",
    scrollCollapse: true,
    paging: false,
    searching: true,
    bInfo: false,
    order: [3, "desc"],
    language: {
      search: "Buscar:",
      searchPlaceholder: "Digite seu município aqui",
    },
  });
}

document.addEventListener('DOMContentLoaded', function() {
  var url = window.location.href.split('/')[3]
  if (url === 'covid19') {
    startCovid19Table();
  }
})