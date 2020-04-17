jQuery(document).ready(function() {
  dt = $('.mdl-data-table').DataTable({
    "scrollY":        "600px",
    "scrollCollapse": true,
    "paging":         false,
    "searching":      true,
    "bInfo":          false,
    "order": [3, "desc"],
  });
});
