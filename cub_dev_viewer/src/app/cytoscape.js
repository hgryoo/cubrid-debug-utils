import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

cytoscape.use( dagre );

export default function loadCyto() {
    var cy = cytoscape({
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
                    'label': 'data(type)'
                },
                selector: '.pt_node',
                style: {
                    'background-color': 'green'
                },
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

        elements: fetch("static/result.cjson").then(res => res.json())
    });

    cy.on('ready', function (event) {
        var pt_nodes = cy.filter('node');

        for (let i = 0; i < pt_nodes.length; ++i) {
            var node = pt_nodes[i];
            var data = node._private.data;

            if (data["type"] == "PT_NODE") {
                node.classes('node pt_node');
            }

            //console.log(pt_nodes[i]._private.data);
        }
    });

    cy.on('click', 'node', function (evt) {
        var node = evt.target;
        console.log(node.json().data);
    });
}