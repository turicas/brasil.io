/* Bootstrap 5 JS included */
/* vanillajs-datepicker 1.1.4 JS included */

/**
* English translation
*/
Datepicker.locales.en = {
    months: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
    monthsShort: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
    days: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sabádo'],
    daysShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'],
    daysMin: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'],
    today: "Hoje",
    clear: "Apagar",
    titleFormat: "MM y",
    format: "dd/mm/yyyy",
    weekStart: 0
}

function getDatePickerTitle (elem) {
    // From the label or the aria-label
    const label = elem.nextElementSibling;
    let titleText = '';
    if (label && label.tagName === 'LABEL') {
        titleText = label.textContent;
    } else {
        titleText = elem.getAttribute('aria-label') || '';
    }
    return titleText;
}

const elems = document.querySelectorAll('.datepicker_input');
for (const elem of elems) {
    const datepicker = new Datepicker(elem, {
        'format': 'yyyy-mm-dd',
        title: getDatePickerTitle(elem),
        minDate: elem.dataset.minDate,
        maxDate: elem.dataset.maxDate,
    });
}