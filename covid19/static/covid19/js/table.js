var dt;

jQuery(document).ready(function() {
  if (selectedStateId === undefined) {
    var columns = [
      { "width": "14%" },
      { "width": "22%" },
      { "width": "14%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" }
    ];
  }
  else {
    var columns = [
      { "width": "20%" },
      { "width": "30%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" }
    ];
  }
  dt = jQuery('.mdl-data-table').DataTable({
    "autoWidth": false,
    "columns": columns,
    "scrollY":        "600px",
    "scrollX": true,
    "scrollCollapse": true,
    "paging":         false,
    "searching":      true,
    "bInfo":          false,
    "order": [3, "desc"],
    "language": {
      search: "&nbsp;&nbsp;Buscar:",
      searchPlaceholder: "Digite seu município aqui",
    },
  });
});
