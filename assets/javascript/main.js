var url = window.location.pathname,
    urlRegExp = new RegExp(url == '/' ? window.location.origin + '/?$' : url.replace(/\/$/, ''));

$('#pagenav a').each(function() {
    if (urlRegExp.test(this.href.replace(/\/$/, '')))
        $(this).find('li').addClass('active');
});

