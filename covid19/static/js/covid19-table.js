var dt;

jQuery(document).ready(function() {
  dt = jQuery('.mdl-data-table').DataTable({
    "autoWidth": false,
    "columns": [
      { "width": "18%" },
      { "width": "18%" },
      { "width": "14%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" },
      { "width": "10%" }
    ],
    "scrollY":        "650px",
    "scrollCollapse": true,
    "paging":         false,
    "searching":      true,
    "bInfo":          false,
    "order": [3, "desc"],
    "language": {
      search: "Buscar:",
      searchPlaceholder: "Digite seu município aqui",
    },
  });
});
