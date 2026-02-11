/**
 * @generated SignedSource<<cac9e5c0a0e6bbf30063bbff9c14eb4f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
export type TodoStatsChartRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoStatsChartRelayContainerQuery$data = {
  readonly priorityStats: ReadonlyArray<{
    readonly count: number;
    readonly priority: PriorityEnum;
  }>;
};
export type TodoStatsChartRelayContainerQuery = {
  response: TodoStatsChartRelayContainerQuery$data;
  variables: TodoStatsChartRelayContainerQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
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
];
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoStatsChartRelayContainerQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoStatsChartRelayContainerQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "377656572b34d55f4a27c9e6368b9289",
    "id": null,
    "metadata": {},
    "name": "TodoStatsChartRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoStatsChartRelayContainerQuery {\n  priorityStats {\n    priority\n    count\n  }\n}\n"
  }
};
})();

(node as any).hash = "be40f9e8c867dced51f29cd938e05c98";

export default node;
