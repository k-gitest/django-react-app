/**
 * @generated SignedSource<<4ef97f932c7f38482b1f8be42c801916>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type TodoStatsChartRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoStatsChartRelayContainerQuery$data = {
  readonly " $fragmentSpreads": FragmentRefs<"TodoStatsChartRelayContainer_stats">;
};
export type TodoStatsChartRelayContainerQuery = {
  response: TodoStatsChartRelayContainerQuery$data;
  variables: TodoStatsChartRelayContainerQuery$variables;
};

const node: ConcreteRequest = {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoStatsChartRelayContainerQuery",
    "selections": [
      {
        "args": null,
        "kind": "FragmentSpread",
        "name": "TodoStatsChartRelayContainer_stats"
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoStatsChartRelayContainerQuery",
    "selections": [
      {
        "alias": null,
        "args": null,
        "concreteType": "PriorityStatsType",
        "kind": "LinkedField",
        "name": "priorityStats",
        "plural": true,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "priority",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "count",
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "5e39d1d3147820fba613986316a13317",
    "id": null,
    "metadata": {},
    "name": "TodoStatsChartRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoStatsChartRelayContainerQuery {\n  ...TodoStatsChartRelayContainer_stats\n}\n\nfragment TodoStatsChartRelayContainer_stats on Query {\n  priorityStats {\n    priority\n    count\n  }\n}\n"
  }
};

(node as any).hash = "e24c7c509d80d9bb13122d30f2a69a33";

export default node;
