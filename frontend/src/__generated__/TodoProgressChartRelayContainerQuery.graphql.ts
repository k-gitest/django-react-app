/**
 * @generated SignedSource<<139a7fbd26da5782e1a9b566193edf27>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type TodoProgressChartRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoProgressChartRelayContainerQuery$data = {
  readonly progressStats: {
    readonly range020: number;
    readonly range2140: number;
    readonly range4160: number;
    readonly range6180: number;
    readonly range81100: number;
  };
};
export type TodoProgressChartRelayContainerQuery = {
  response: TodoProgressChartRelayContainerQuery$data;
  variables: TodoProgressChartRelayContainerQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "ProgressStatsType",
    "kind": "LinkedField",
    "name": "progressStats",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "range020",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "range2140",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "range4160",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "range6180",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "range81100",
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
    "name": "TodoProgressChartRelayContainerQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoProgressChartRelayContainerQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "4de74201b59be2505124dd9820828ae0",
    "id": null,
    "metadata": {},
    "name": "TodoProgressChartRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoProgressChartRelayContainerQuery {\n  progressStats {\n    range020\n    range2140\n    range4160\n    range6180\n    range81100\n  }\n}\n"
  }
};
})();

(node as any).hash = "222e6b35056290ac84e606bbb1a2580d";

export default node;
