var cityData, cityGeoJSON, cityLayer, colors, map, selectedVar, stateGeoJSON, stateLayer;
selectedVar = "confirmed";
colors = {
  "confirmed": "#00F",
  "confirmed_per_100k_inhabitants": "#80F",
  "deaths": "#F00",
  "death_rate": "#F08",
};
zeroText = {
  "confirmed": "Nenhum",
  "confirmed_per_100k_inhabitants": "Nenhum",
  "deaths": "Nenhuma",
  "death_rate": "Nenhuma",
};

function opacityFromValue(value, maxValue) {
  return Math.log2(value + 1) / Math.log2(maxValue + 1);
}
function valueFromOpacity(opacity, maxValue) {
  return parseInt(2 ** (opacity * Math.log2(maxValue + 1)) - 1);
}
function cityStyle(feature) {
  var value = cityData[feature.id][selectedVar] || 0;
  var maxValue = maxValues[selectedVar];
  var opacity = opacityFromValue(value, maxValue);
  return {
    color: "#000",
    fillColor: colors[selectedVar],
    fillOpacity: opacity,
    lineJoin: "round",
    opacity: 0,
    weight: 1,
  }
}
function stateStyle(feature) {
  return {
    color: "#000",
    fillColor: "#FFF",
    fillOpacity: 0.1,
    lineJoin: "round",
    opacity: 1,
    weight: 0.5
  };
}

function createMap() {
  map = L.map("map", {
    zoomSnap: 0.25,
    zoomDelta: 0.25,
    minZoom: 4.5,
    maxZoom: 7,
    attributionControl: false
  });
  map.setView([-15, -54], 4.75);
}
function updateMap() {
  var hasToAddStateLayer = stateGeoJSON !== undefined && stateLayer === undefined;
  var hasToAddCityLayer = (stateLayer !== undefined || hasToAddStateLayer) && cityGeoJSON !== undefined && cityLayer === undefined;
  var hasToAddLegendLayer = (stateLayer !== undefined || hasToAddStateLayer) && (cityLayer !== undefined || hasToAddCityLayer);

  if (hasToAddStateLayer) {
    stateLayer = L.geoJSON(stateGeoJSON, {style: stateStyle}).addTo(map);
  }

  if (hasToAddCityLayer) {
    cityGeoJSON.features = cityGeoJSON.features.filter(function (item) {
      var city = cityData[item.id];
      return city !== undefined;
    });
    cityLayer = L.geoJSON(
      cityGeoJSON,
      {
        style: cityStyle,
        onEachFeature: function (feature, layer) {
          layer.on("mouseover", function () {
            this.setStyle({opacity: 1});
          });
          layer.on("mouseout", function () {
            this.setStyle({opacity: 0});
          });
        }
      }
    ).addTo(map);
  }

  if (hasToAddLegendLayer) {
    var legend = L.control({position: "bottomright"});
    legend.onAdd = function (map) {
      var div = L.DomUtil.create("div", "info legend");
      var lastValue, displayValue;
      var maxValue = maxValues[selectedVar];
      var color = colors[selectedVar];
      var zeroDisplay = zeroText[selectedVar];
      for (var opacity = 0; opacity <= 1; opacity += 0.25) {
        var value = valueFromOpacity(opacity, maxValue);
        if (lastValue === undefined) {
          displayValue = zeroDisplay;
        }
        else {
          displayValue = `${lastValue} &mdash; ${value}`;
        }
        div.innerHTML += `<i style="background: ${color}; opacity: ${opacity}"></i> ${displayValue} <br>`;
        lastValue = value;
      }
      return div;
    };
    legend.addTo(map);
  }
}

function retrieveData() {
  jQuery.getJSON(
    dataURL.cities,
    function (data) {
      cityData = data.cities;
      maxValues = data.max;
      updateMap();
    }
  );
  jQuery.getJSON(
    dataURL.stateGeoJSON,
    function (data) {
      stateGeoJSON = data;
      updateMap();
    }
  );
  jQuery.getJSON(
    dataURL.cityGeoJSON,
    function (data) {
      cityGeoJSON = data;
      updateMap();
    }
  );
}

jQuery(document).ready(function() {
  createMap();
  retrieveData();
});
