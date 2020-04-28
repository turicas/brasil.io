var cityData,
    cityGeoJSON,
    cityLayer,
    totalData,
    totalId,
    dataConfig,
    legendBins,
    map,
    placeDataControl,
    legendControl,
    selectedPlace,
    selectedVar,
    stateGeoJSON,
    stateLayer,
    varControl;

dataConfig = {
  "confirmed_per_100k_inhabitants": {
    "color": "#2B580C",
    "displayText": "Confirmados/100.000 hab.",
    "zeroText": "Nenhum",
  },
  "deaths_per_100k_inhabitants": {
    "color": "#F39",
    "displayText": "Óbitos/100.000 hab.",
    "zeroText": "Nenhum",
  },
  "death_rate_percent": {
    "color": "#F08",
    "displayText": "Letalidade",
    "zeroText": "Nenhum",
  },
  "confirmed": {
    "color": "#00F",
    "displayText": "Casos confirmados",
    "zeroText": "Nenhum",
  },
  "deaths": {
    "color": "#F00",
    "displayText": "Óbitos confirmados",
    "zeroText": "Nenhum",
  },
};

legendBins = 6;
totalId = 0; // Brasil or state
selectedPlace = totalId;
selectedVar = Object.keys(dataConfig)[0];

function mapType() {
  return selectedStateId === undefined ? "country" : "state";
}
function getPlaceData(place) {
  return place == totalId ? totalData : cityData[place];
}
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
    fillColor: dataConfig[selectedVar].color,
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
    weight: 0.75
  };
}
function changeVar(newVar) {
  selectedVar = newVar;
  cityLayer.setStyle(cityStyle);
  updateLegendControl();
}

function updateLegendControl() {
  var color = dataConfig[selectedVar].color,
      displayValue,
      div = legendControl.getContainer(),
      labels = [`<b>${dataConfig[selectedVar].displayText}</b>`, "<br><br>"],
      lastOpacity,
      maxValue = maxValues[selectedVar],
      zeroDisplay = dataConfig[selectedVar].zeroText;

  for (var counter = 0; counter <= legendBins; counter += 1) {
    var opacity = counter / legendBins;
    var value = valueFromOpacity(opacity, maxValue);
    var lastValue = lastOpacity === undefined ? 0 : valueFromOpacity(lastOpacity, maxValue);
    if (lastOpacity === undefined || lastValue != value) {
      displayValue = lastOpacity === undefined ? zeroDisplay : `${lastValue} &mdash; ${value}`;
      labels.push(`<span class="valign-wrapper"> <i style="background: ${color}; opacity: ${opacity}"></i> ${displayValue} </span>`);
    }
    lastOpacity = opacity;
  }
  div.innerHTML = labels.join("");
}
function updatePlaceDataControl(placeData) {
  var div = placeDataControl.getContainer();
  var dataLines = [];
  Object.keys(dataConfig).forEach(function(item) {
    var value = Intl.NumberFormat("pt-BR").format(placeData[item]);
    value = item.endsWith("percent") ? `${value}%` : value;
    dataLines.push(`<dt>${dataConfig[item].displayText}:</dt> <dd>${value}</dd>`);
  });
  div.innerHTML = `
    <b>${placeData.city}</b>
    <br>
    <dl>
      ${dataLines.join("\n")}
    </dl>
  `;
}
function updateVarControl() {
  var div = varControl.getContainer();
  var inputs = ["<b>Selecione a variável</b>"];
  Object.keys(dataConfig).forEach(function(item) {
    inputs.push(`<label><input type="radio" class="radio-control" name="radio-var-control" value="${item}"><span>${dataConfig[item].displayText}</span></label>`);
  });
  div.innerHTML = inputs.join("<br>");
  jQuery(".radio-control").change(function() {
    changeVar(jQuery(this).val());
  });
}

function createMap() {
  var minZoom = mapType() == "country" ? 4.5 : 6;
  var maxZoom = mapType() == "country" ? 8 : 12;
  map = L.map("map", {
    zoomSnap: 0.25,
    zoomDelta: 0.25,
    minZoom: minZoom,
    maxZoom: maxZoom,
    attributionControl: false
  });
  map.setView([-15, -54], minZoom);
}
function hasToAddStateLayer() {
  return stateGeoJSON !== undefined && stateLayer === undefined;
}
function hasToAddCityLayer() {
  return stateLayer !== undefined && cityGeoJSON !== undefined && cityLayer === undefined;
}
function hasToAddLegendLayer() {
  return stateLayer !== undefined && cityLayer !== undefined;
}
function mapHasLoaded() {
  return stateLayer !== undefined && cityLayer !== undefined;
}
function mapFit() {
  map.fitBounds(stateLayer.getBounds());
}
function updateMap() {
  if (hasToAddStateLayer()) {
    if (mapType() == "country") {
      stateLayer = L.geoJSON(stateGeoJSON, {style: stateStyle}).addTo(map);
    }
    else if (mapType() == "state") {
      var filteredStateGeoJSON = stateGeoJSON;
      filteredStateGeoJSON.features = filteredStateGeoJSON.features.filter(function (item) {
        return item.properties.CD_GEOCUF == selectedStateId;
      });
      stateLayer = L.geoJSON(filteredStateGeoJSON, {style: stateStyle}).addTo(map);
    }
    mapFit();
  }

  if (hasToAddCityLayer()) {
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
            updatePlaceDataControl(getPlaceData(this.feature.id));
          });
          layer.on("mouseout", function () {
            this.setStyle({opacity: 0});
            updatePlaceDataControl(getPlaceData(totalId));
          });
        }
      }
    ).addTo(map);
  }

  if (hasToAddLegendLayer()) {
    notesControl = L.control({position: "bottomleft"});
    notesControl.onAdd = function (map) {
      var div = L.DomUtil.create("div", "info legend");
      div.innerHTML = 'Fonte: Secretarias Estaduais de Saúde'
      div.innerHTML += '<br>Coleta e análise: <a href="https://brasil.io/">Brasil.IO</a>';
      return div;
    };
    notesControl.addTo(map);

    legendControl = L.control({position: "bottomleft"});
    legendControl.onAdd = function (map) {
      var div = L.DomUtil.create("div", "info legend");
      return div;
    };
    legendControl.addTo(map);
    updateLegendControl();

    placeDataControl = L.control({position: "bottomright"});
    placeDataControl.onAdd = function (map) {
      var div = L.DomUtil.create("div", "info legend");
      return div;
    };
    placeDataControl.addTo(map);
    updatePlaceDataControl(getPlaceData(selectedPlace));

    varControl = L.control({position: "topright"});
    varControl.onAdd = function (map) {
      var div = L.DomUtil.create("div", "info legend");
      return div;
    };
    varControl.addTo(map);
    updateVarControl();
  }

  if (mapHasLoaded()) {
    mapLoaded();
  }
}

function mapLoaded() {
  jQuery("#loading").css("z-index", -999);
  jQuery(".radio-control:first").prop("checked", true).trigger("click");
}

function retrieveData() {
  jQuery.getJSON(
    dataURL.cities,
    function (data) {
      cityData = data.cities;
      maxValues = data.max;
      totalData = data.total;
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

  jQuery(window).resize(function() {
    if (jQuery(window).width() > 1840) {
      jQuery("#table-col").removeClass("xl12").addClass("xl6");
      jQuery("#map-col").removeClass("xl12").addClass("xl6");
    }
    else {
      jQuery("#table-col").removeClass("xl6").addClass("xl12");
      jQuery("#map-col").removeClass("xl6").addClass("xl12");
    }
    dt.columns.adjust();
  });
  window.dispatchEvent(new Event("resize"));
});
