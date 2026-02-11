/**
 * @generated SignedSource<<8c0d9c9f52e46d143cdeff3933abaea1>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
export type TodoListRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoListRelayContainerQuery$data = {
  readonly todos: ReadonlyArray<{
    readonly id: string;
    readonly priority: PriorityEnum;
    readonly progress: number;
    readonly todoTitle: string;
    readonly updatedAt: any;
  }>;
};
export type TodoListRelayContainerQuery = {
  response: TodoListRelayContainerQuery$data;
  variables: TodoListRelayContainerQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "TodoType",
    "kind": "LinkedField",
    "name": "todos",
    "plural": true,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "id",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "todoTitle",
        "storageKey": null
      },
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
        "name": "progress",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "updatedAt",
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
    "name": "TodoListRelayContainerQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoListRelayContainerQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "d2e38b6897df2d87272c1757b4ac5ae1",
    "id": null,
    "metadata": {},
    "name": "TodoListRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoListRelayContainerQuery {\n  todos {\n    id\n    todoTitle\n    priority\n    progress\n    updatedAt\n  }\n}\n"
  }
};
})();

(node as any).hash = "e29d00ca057c7008a81d56156db515db";

export default node;
