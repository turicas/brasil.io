function placeType() {
  return selectedStateId === undefined ? "country" : "state";
}
function linearOpacityFromValue(value, maxValue) {
  return value / maxValue;
}
function linearValueFromOpacity(opacity, maxValue) {
  return parseInt(opacity * maxValue);
}
function log2OpacityFromValue(value, maxValue) {
  return Math.log2(value + 1) / Math.log2(maxValue + 1);
}
function log2ValueFromOpacity(opacity, maxValue) {
  return parseInt(2 ** (opacity * Math.log2(maxValue + 1)) - 1);
}

var dataConfig = {
  "confirmed_per_100k_inhabitants": {
    "color": "#2B580C",
    "displayText": "Confirmados/100.000 hab.",
    "zeroText": "Nenhum",
    "opacityFromValue": log2OpacityFromValue,
    "valueFromOpacity": log2ValueFromOpacity,
  },
  "deaths_per_100k_inhabitants": {
    "color": "#F39",
    "displayText": "Óbitos/100.000 hab.",
    "zeroText": "Nenhum",
    "opacityFromValue": log2OpacityFromValue,
    "valueFromOpacity": log2ValueFromOpacity,
  },
  "death_rate_percent": {
    "color": "#F08",
    "displayText": "Letalidade",
    "zeroText": "Nenhum",
    "opacityFromValue": linearOpacityFromValue,
    "valueFromOpacity": linearValueFromOpacity,
  },
  "confirmed": {
    "color": "#00F",
    "displayText": "Casos confirmados",
    "zeroText": "Nenhum",
    "opacityFromValue": log2OpacityFromValue,
    "valueFromOpacity": log2ValueFromOpacity,
  },
  "deaths": {
    "color": "#F00",
    "displayText": "Óbitos confirmados",
    "zeroText": "Nenhum",
    "opacityFromValue": log2OpacityFromValue,
    "valueFromOpacity": log2ValueFromOpacity,
  },
};
