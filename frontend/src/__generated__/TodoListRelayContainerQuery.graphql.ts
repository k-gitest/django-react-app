/**
 * @generated SignedSource<<f7018f9bebca5585038db3ab76cfa5d1>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type TodoListRelayContainerQuery$variables = Record<PropertyKey, never>;
export type TodoListRelayContainerQuery$data = {
  readonly todos: ReadonlyArray<{
    readonly id: string;
    readonly " $fragmentSpreads": FragmentRefs<"TodoItemRelayContainer_todo">;
  }>;
};
export type TodoListRelayContainerQuery = {
  response: TodoListRelayContainerQuery$data;
  variables: TodoListRelayContainerQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoListRelayContainerQuery",
    "selections": [
      {
        "alias": null,
        "args": null,
        "concreteType": "TodoType",
        "kind": "LinkedField",
        "name": "todos",
        "plural": true,
        "selections": [
          (v0/*: any*/),
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "TodoItemRelayContainer_todo"
          }
        ],
        "storageKey": null
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "TodoListRelayContainerQuery",
    "selections": [
      {
        "alias": null,
        "args": null,
        "concreteType": "TodoType",
        "kind": "LinkedField",
        "name": "todos",
        "plural": true,
        "selections": [
          (v0/*: any*/),
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
    ]
  },
  "params": {
    "cacheID": "8c8debf1b8758287933278458a3b1d0a",
    "id": null,
    "metadata": {},
    "name": "TodoListRelayContainerQuery",
    "operationKind": "query",
    "text": "query TodoListRelayContainerQuery {\n  todos {\n    id\n    ...TodoItemRelayContainer_todo\n  }\n}\n\nfragment TodoEditModalRelayContainer_todo on TodoType {\n  id\n  todoTitle\n  priority\n  progress\n}\n\nfragment TodoItemRelayContainer_todo on TodoType {\n  id\n  todoTitle\n  priority\n  progress\n  updatedAt\n  ...TodoEditModalRelayContainer_todo\n}\n"
  }
};
})();

(node as any).hash = "2516ba00a5a9122eb18b747b9a6ea204";

export default node;
