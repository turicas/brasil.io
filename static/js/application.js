/**
 * JS used to start UI components
 *
 *
 */

$(document).ready(function(){
  $('.sidenav').sidenav({
    onOpenStart: function() {
      $('.sidenav-trigger[data-target="' + this.el.id + '"]')
        .attr('aria-expanded', 'true')
        .attr('aria-label', 'Fechar menu de navegação');
    },
    onCloseStart: function() {
      $('.sidenav-trigger[data-target="' + this.el.id + '"]')
        .attr('aria-expanded', 'false')
        .attr('aria-label', 'Abrir menu de navegação');
    }
  });

  $(window).on('resize', function() {
    if (window.innerWidth >= 993) {
      $('.sidenav').sidenav('close');
    }
  });
});
