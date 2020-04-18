var cityData,
    cityGeoJSON,
    cityLayer,
    colors,
    countryData,
    countryId,
    displayText,
    legendBins,
    map,
    placeDataControl,
    legendControl,
    selectedPlace,
    selectedVar,
    stateGeoJSON,
    stateLayer,
    varControl;

colors = {
  "confirmed": "#00F",
  "confirmed_per_100k_inhabitants": "#2B580C",
  "deaths": "#F00",
  "death_rate_percent": "#F08",
};
displayText = {
  "confirmed": "Casos confirmados",
  "confirmed_per_100k_inhabitants": "Confirmados/100.000 hab.",
  "deaths": "Óbitos confirmados",
  "death_rate_percent": "Taxa de mortalidade",
};
legendBins = 5;
countryId = 0; // Brasil
selectedPlace = countryId;
selectedVar = "confirmed";
zeroText = {
  "confirmed": "Nenhum",
  "confirmed_per_100k_inhabitants": "Nenhum",
  "deaths": "Nenhum",
  "death_rate_percent": "Nenhum",
};

function getPlaceData(place) {
  return place == countryId ? countryData : cityData[place];
}
function opacityFromValue(value, maxValue) {
  // TODO: should round opacity numbers to bin value in legend?
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
function changeVar(newVar) {
  selectedVar = newVar;
  cityLayer.setStyle(cityStyle);
  updateLegendControl();
}

function updateLegendControl() {
  var div = legendControl.getContainer();
  var lastValue, displayValue;
  var maxValue = maxValues[selectedVar];
  var color = colors[selectedVar];
  var zeroDisplay = zeroText[selectedVar];
  var labels = [`<b>${displayText[selectedVar]}</b>`, ""];
  for (var opacity = 0; opacity <= 1; opacity += 1.0 / legendBins) {
    var value = valueFromOpacity(opacity, maxValue);
    displayValue = lastValue === undefined ? zeroDisplay : `${lastValue} &mdash; ${value}`;
    labels.push(`<i style="background: ${color}; opacity: ${opacity}"></i> ${displayValue}`);
    lastValue = value + 1;
  }
  div.innerHTML = labels.join("<br>");
}
function updatePlaceDataControl(placeData) {
  var div = placeDataControl.getContainer();
  var dataLines = [];
  Object.keys(displayText).forEach(function(item) {
    var value = Intl.NumberFormat("pt-BR").format(placeData[item]);
    value = item.endsWith("percent") ? `${value}%` : value;
    dataLines.push(`<dt>${displayText[item]}:</dt> <dd>${value}</dd>`);
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
  var inputs = [];
  Object.keys(displayText).forEach(function(item) {
    inputs.push(`<label><input type="radio" class="radio-control" name="radio-var-control" value="${item}"><span>${displayText[item]}</span></label>`);
  });
  div.innerHTML = inputs.join("<br>");
  jQuery(".radio-control").change(function() {
    changeVar(jQuery(this).val());
  });
}

function createMap() {
  map = L.map("map", {
    zoomSnap: 0.25,
    zoomDelta: 0.25,
    minZoom: 4.5,
    maxZoom: 9,
    attributionControl: false
  });
  map.setView([-15, -54], 4.75);
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
function updateMap() {
  if (hasToAddStateLayer()) {
    stateLayer = L.geoJSON(stateGeoJSON, {style: stateStyle}).addTo(map);
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
            updatePlaceDataControl(getPlaceData(countryId));
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
      countryData = data.total;
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
  });
  window.dispatchEvent(new Event("resize"));
});
