/**
 * @generated SignedSource<<db2d27755fe33ecfb218182bb81f6bac>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type TodoProgressChartRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoProgressChartRelayContainerQuery$data = {
  readonly " $fragmentSpreads": FragmentRefs<"TodoProgressChartRelayContainer_progress">;
};
export type TodoProgressChartRelayContainerQuery = {
  response: TodoProgressChartRelayContainerQuery$data;
  variables: TodoProgressChartRelayContainerQuery$variables;
};

const node: ConcreteRequest = {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoProgressChartRelayContainerQuery",
    "selections": [
      {
        "args": null,
        "kind": "FragmentSpread",
        "name": "TodoProgressChartRelayContainer_progress"
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoProgressChartRelayContainerQuery",
    "selections": [
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
    ]
  },
  "params": {
    "cacheID": "5bfbbfc36069074bc615f4051bf7b616",
    "id": null,
    "metadata": {},
    "name": "TodoProgressChartRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoProgressChartRelayContainerQuery {\n  ...TodoProgressChartRelayContainer_progress\n}\n\nfragment TodoProgressChartRelayContainer_progress on Query {\n  progressStats {\n    range020\n    range2140\n    range4160\n    range6180\n    range81100\n  }\n}\n"
  }
};

(node as any).hash = "4092f3fa974891856fdb86602cf3e595";

export default node;
