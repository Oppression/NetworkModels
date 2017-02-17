o3 = {}
o3.loadData = function() {
  var svg = d3.select("svg"),
      width = +svg.attr("width"),
      height = +svg.attr("height");

  var color = d3.scaleOrdinal(d3.schemeCategory20);

  var simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(function(d) { return d.id; }))
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(width / 2, height / 2));

  d3.json("sample_data.json", renderSampleData);

  function renderSampleData(error, graph) {
    if (error) throw error;

    var link = svg.append("g")
        .attr("class", "links")
      .selectAll("line")
      .data(graph.links)
      .enter().append("line")
        .attr("stroke-length", function(d) { return d.value; });

    var node = svg.append("g")
        .attr("class", "node")
      .selectAll("circle")
      .data(graph.nodes)
      .enter().append("circle")
        .attr("r", 8)
        .attr("fill", function(d) {
          return color(d.group);
        })
       .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
            // .on('dblclick', connectedNodes)); //Added code

    node.append("title")
        .text(function(d) { return d.id; });

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    function ticked() {
      link
          .attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });

      node
          .attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; });
    }
    var optArray = [];

    for (var i = 0; i < graph.nodes.length - 1; i++) {
        optArray.push(graph.nodes[i].name);
    }
    optArray = optArray.sort();
    (function () {
        ("#search").autocomplete({
            source: optArray
        });
    });

  }

  function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  function searchNode() {
      //find the node
      var selectedVal = document.getElementById('search').value;
      var node = svg.selectAll(".node circle");
      if (selectedVal == "none") {
          node.style("stroke", "white").style("stroke-width", "1");
      } else {
          var selected = node.filter(function (d, i) {
              return d.id != selectedVal;
          });
          selected.style("opacity", "0");
          var link = svg.selectAll(".link")
          link.style("opacity", "0");
          d3.selectAll(".node, .link").transition()
              .duration(5000)
              .style("opacity", 1);
      }
  }

      d3.select("#search_button")
      .on("click", searchNode);
}
