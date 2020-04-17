var dt, map, statesGeoJSON, citiesGeoJSON;
var cityLayer, stateLayer;
var selectedVar = "confirmed";
var colors = {
	"confirmed": "#5500FF",
	"deaths": "#FF0000",
};
function defineOpacity(value, maxValue) {
	if (value == 0) {
		return 0;
	}
	else if (value == maxValue) {
		return 10;
	}
	else {
		return Math.log2(value + 1) / Math.log2(maxValue + 1);
	}
}

function cityStyle(feature) {
	var value = cityValues[selectedVar][parseInt(feature.properties.CD_GEOCMU)] || 0;
	var maxValue = maxValues[selectedVar];
	var opacity = defineOpacity(value, maxValue);
	return {
		lineJoin: "round",
		weight: 0.25,
		opacity: 0,
		fillOpacity: opacity,
		color: colors[selectedVar],
	}
}
function stateStyle(feature) {
	return {
		color: "#000000",
		fillColor: "#FFFFFF",
		fillOpacity: 0.1,
		opacity: 1,
		weight: 0.5
	};
}
jQuery(document).ready(function() {
	map = L.map("map", {
		zoomSnap: 0.25,
		zoomDelta: 0.25,
		minZoom: 4.75,
		maxZoom: 9,
		attributionControl: false
	});
	map.setView([-15, -54], 4.75);
	jQuery.getJSON(
		"https://data.brasil.io/dataset/shapefiles-brasil/0.05/BR-UF.geojson",
		function (data) {
			statesGeoJSON = data;
			stateLayer = L.geoJSON(data, {style: stateStyle}).addTo(map);

			jQuery.getJSON(
				"https://data.brasil.io/dataset/shapefiles-brasil/0.01/BR-municipios.geojson",
				function (data) {
					citiesGeoJSON = data;
					data.features = data.features.filter(function (item) {
						return cityValues[selectedVar][parseInt(item.properties.CD_GEOCMU)] !== undefined;
					});
					cityLayer = L.geoJSON(data, {style: cityStyle}).addTo(map);
				}
			);
		}
	);
	var legend = L.control({position: "bottomright"});
	legend.onAdd = function (map) {
		var div = L.DomUtil.create("div", "info legend");
		var lastValue = 0;
		for (var i = 0; i <= 1; i += 0.1) {
			value = parseInt(2 ** (i * Math.log2(maxValues[selectedVar] + 1)) - 1);
			div.innerHTML += '<i style="background: ' + colors[selectedVar] + '; opacity: ' + i + '"></i> ' + lastValue + '&mdash;' + value + '<br>';
			lastValue = value;
		}
		return div;
	};
	legend.addTo(map);
});
