var dt;

jQuery(document).ready(function() {
  dt = jQuery('.mdl-data-table').DataTable({
    "scrollY":        "600px",
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
