(function ($) {
    // Extends pseido selectos, adds case insesitive contains
    $.expr[":"].icontains = $.expr.createPseudo(function(arg) {
        return function( elem ) {
            return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
        };
    });

    var filtering = function(e) {
      var selector, value;
      value = $(this).val();
      if (value) {
        selector = ".graph-item:not(:has(.graph-title:has(a:icontains("+ value +"))))";
        $(selector).hide();
      } else {
        $(".graph-item").show();
      }
    };
    $("#graphs-filter").on("keypress", filtering);
    $("#graphs-filter").on("change", filtering);
    $("#graphs-filter").on("blur", filtering);

    var sizeFormat = function(bytecount) {
        var str = bytecount+' B';
        if (Number(bytecount) > 1000) { str = (bytecount/1000).toFixed(2)+' kB'; }
        if (Number(bytecount) > 1000000) { str = (bytecount/1000000).toFixed(2)+' MB'; }
        if (Number(bytecount) > 1000000000) { str = (bytecount/1000000000).toFixed(2)+' GB'; }
        if (Number(bytecount) > 1000000000000) { str = (bytecount/1000000000000).toFixed(2)+' TB'; }
        return str;
    };

    var init = function() {
        (function basic_bubble(container) {
          var
            d1 = [],
            d2 = [],
            point, graph, i;

          for (i = 0; i < 10; i++ ){
            point = [i, Math.ceil(Math.random()*10), Math.ceil(Math.random()*10)];
            d1.push(point);

            point = [i, Math.ceil(Math.random()*10), Math.ceil(Math.random()*10)];
            d2.push(point);
          }
          var series = {
            owned: {
                data: [],
                lines: {show: false },
                points: {show: false },
                bubbles : { show : true },
                markers: {
                  show: true,
                  position: 'cm',
                  fontSize: 11,
                  labelFormatter : function (o) { return labels[o.index]; }
                }
            },
            collaboration: {
                data: [],
                lines: {show: false },
                points: {show: false },
                bubbles : { show : true },
                markers: {
                  show: true,
                  position: 'cm',
                  fontSize: 11,
                  labelFormatter : function (o) { return labels[o.index]; }
                }
            }
          };
          var labels = [];
          var nodes = [];
          var relationships = [];
          var storages = [];
          var storagesValues = [];
          $("input[type=\"hidden\"].stats-series").each(function (e) {
            var serie = JSON.parse($(this).val());
            if (serie.nodes + serie.relationships > 0) {
                var values = [serie.nodes, serie.relationships, serie.storage];
                series[serie.type].data.push(values);
                series[serie.type].label = serie.label;
                labels.push(serie.title +" ("+ sizeFormat(serie.storage) +")");
                nodes.push(serie.nodes);
                relationships.push(serie.relationships);
                storages.push(serie.storage);
            }

          });
          // Normalization of storage values
          var node = {
            max: _.max(nodes),
            min: _.min(nodes)
          };
          var relationship = {
            max: _.max(relationships),
            min: _.min(relationships)
          };
          var storageMax = Math.max(node.max, relationship.max);
          var storageMin = Math.min(node.min, relationship.min);
          var storage = {
            max: _.max(storages),
            min: _.min(storages)
          };
          var owned = series.owned.data;
          series.owned.data = [];
          Flotr._.each(owned, function (point) {
              point[2] = (point[2] * (storageMax - storageMin)) / ((storage.max - storage.min) || 1);
              series.owned.data.push(point);
              storagesValues.push(point[2]);
          });
          var collaboration = series.collaboration.data;
          series.collaboration.data = [];
          Flotr._.each(collaboration , function (point) {
              point[2] = (point[2] * (storageMax - storageMin)) / ((storage.max - storage.min) || 1);
              series.collaboration.data.push(point);
              storagesValues.push(point[2]);
          });

          var storageMean = _.reduce(storagesValues, function(a, b){ return a + b; }, 0) / storagesValues.length;
          var storagesValuesMax = _.max(storagesValues);
          var normalizedAverage = (storageMean / storagesValuesMax) * 0.1;

          // Draw the graph
          graph = Flotr.draw(container, [series.owned, series.collaboration], {
            bubbles : { show : true, baseRadius : normalizedAverage },
            yaxis   : { min : relationship.min - storageMean, max : relationship.max + storageMean },
            xaxis   : { min : node.min - storageMean, max : node.max + storageMean},
            mouse: {
                track: true
            }
          });
        })(document.getElementById("dashboardStats"));
    };
    $(document).ready(init);
})(jQuery.noConflict());
