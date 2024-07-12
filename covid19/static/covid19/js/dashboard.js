// State selector EventListner
document.querySelector("#state-select").addEventListener("change", function (e) {
    e.target.value ? window.location = e.target.value : false;
});

// Getting all necessary django template vars
const dashVars = {};
document.querySelectorAll("script[type='application/json']").forEach(el => {
    dashVars[`${el.id}`] = JSON.parse(document.getElementById(el.id).textContent);
})

const dataURL = {
    cities: dashVars.citiesCases,
    stateGeoJSON: dashVars.statesGeo,
    cityGeoJSON: dashVars.citiesGeo,
    historicalDaily: dashVars.historicalDaily,
    historicalWeekly: dashVars.historicalWeekly,
},
    selectedStateId = dashVars.stateId ? dashVars.stateId : undefined,
    selectedStateAcronym = dashVars.stateId ? dashVars.state : undefined,
    selectedCitySlug = dashVars.cityId != "" ? dashVars.citySlug : undefined;

// Putting ?state=StateAcronym if necessary in dataURLs
for (const el in dataURL) {
    const state = dashVars.state;
    dataURL[el] = state && state != "" ? dataURL[el] + "?state=" + state : dataURL[el];
}

function skeletonsGenerator(gridClass, templateId, quantity) {
    const grid = document.querySelector(gridClass);
    const template = document.querySelector(templateId);

    for (let i = 0; i < quantity; i++) {
        grid.append(template.content.cloneNode(true));
    }

    return [grid, template];
}

[gridCards, cardTemplate] = skeletonsGenerator('.grid-cards', '#card-template', 6);

const endPoint = "/covid19/country-state/";
const request = dashVars.state ? (endPoint + dashVars.state) : endPoint;

const formatter = new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
});

fetch(request)
    .then(res => res.json())
    .then(data => {
        gridCards.innerHTML = ''
        data.country_aggregate.forEach(res => {
            const div = cardTemplate.content.cloneNode(true)
            div.querySelector('[data-title]').textContent = res.title ? res.title : "";
            div.querySelector('[data-value]').textContent = res.value ? res.value.toLocaleString('pt-BR') : "";
            div.querySelector('[data-percent]').textContent = res.value_percent ? formatter.format(res.value_percent) + " %" : "";
            div.querySelector('[data-bs-toggle]').title = res.tooltip ? res.tooltip : "";
            gridCards.append(div)
        })

        // Activating tolltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })
    })