var Brasilio = {}

Brasilio.pullDatasets = function() {
    let url = 'api/datasets'
    $.get(url,function(data){
        Brasilio.renderDatasets(data);
    })
}

Brasilio.renderDatasets = function(results) {
    let $container = $("#datasets")

    results = results.results
    results.forEach(function(dataset){

        link = `dataset/`+ dataset.slug

        var htmlComponent = `
        <div class="col s12 m6">
          <div class="card horizontal small">
            <div class="card-stacked">
              <div class="card-content">
                <span class="card-title activator grey-text text-darken-4">
                  <i class="material-icons left"></i>
                  `+ dataset.name +`
                </span>
                <p>
                  ` + dataset.description + `
                </p>
              </div>
              <div class="card-action">
                <a href="` + link + `">Visualizar</a>
              </div>
            </div>
          </div>
        </div>

        `

        $container.prepend(htmlComponent);
    })

}
