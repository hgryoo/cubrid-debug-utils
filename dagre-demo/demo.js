window.addEventListener('DOMContentLoaded', function() {
    var cy = window.cy = cytoscape({
      container: document.getElementById('cy'),

      boxSelectionEnabled: false,
      autounselectify: true,

      layout: {
        name: 'dagre'
      },

      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#11479e',
            'label': 'data(type)'
          }
        },

        {
          selector: 'edge',
          style: {
            'width': 4,
            'target-arrow-shape': 'triangle',
            'line-color': '#9dbaea',
            'target-arrow-color': '#9dbaea',
            'curve-style': 'bezier',
            'label': 'data(name)'
          }
        }
      ],

      elements: fetch("./result.json").then(res => res.json())
    });
    
    cy.filter(['[node [type = "PT_NODE"]']).style('background-color','green');
    
    cy.on('click', 'node', function(evt){
      var node = evt.target;
      console.log( 'clicked ' + node.id() );
    });

});