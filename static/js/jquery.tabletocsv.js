/**
 * Takes a HTML table and saves its data as a csv
 *
 * copyright (c) 2013 Scott-David Jones
 */
(function($){
	$.fn.tableToCsv = function( options ){
		var t = $(this);
		if (! t.is('table')) {
			throw "selector element is not a table..";
		}
		var settings = $.extend({
			seperator: ',',
			fileName: t.attr('id'),
			outputheaders: true,
			extension: 'csv'
		}, options);
		var csvData = [];
		//get headers
		if (settings.outputheaders === true) {
			var headers = [];
			t.find('thead tr').each(function(index, element){
				var row = $(this);
				row.find('th').each(function(i,e){
					var cell = $(this);
					headers.push('"'+cell.text()+'"');
				});
			});
			csvData.push(headers);
		}
		//get the main body of data
		t.find('tbody tr').each(function(i,e){
			var rowData = [];
			var row = $(this);
			row.find('td').each(function(i, e){
				var cell = $(this);
				var text = cell.text();
				//if number add else encapsulate with quotes
				if ( !isNaN(parseFloat(text)) && isFinite(text) )
				{
					rowData.push(text);
				}
				else
				{
					rowData.push('"'+text+'"');
				}
				
			});
			csvData.push(rowData);
		});
		var csvString = '';
		for (var c in csvData)
		{
			var current = csvData[c];
			csvString += current.join(settings.seperator)+"\r\n";
		}
		//save file
		//seems to be the only way to do this..
		//credit @ Jeremy Banks http://stackoverflow.com/questions/7034754/how-to-set-a-file-name-using-window-open
		var downloadLink = document.createElement('a');
		downloadLink.href = 'data:text/csv;charset=utf-8,'+ escape(csvString);
		downloadLink.download = settings.fileName+"."+settings.extension;
		document.body.appendChild(downloadLink);
		downloadLink.click();
		document.body.removeChild(downloadLink);
	}
}(jQuery));