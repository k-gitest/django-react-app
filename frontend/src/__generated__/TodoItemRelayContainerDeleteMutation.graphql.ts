/**
 * @generated SignedSource<<3b9b14016d2f585b3afde6f6dc184791>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ErrorCategory = "AUTHENTICATION" | "AUTHORIZATION" | "CONFLICT" | "EXTERNAL_SERVICE" | "INTERNAL" | "NOT_FOUND" | "RATE_LIMIT" | "VALIDATION" | "%future added value";
export type TodoItemRelayContainerDeleteMutation$variables = {
  id: string;
};
export type TodoItemRelayContainerDeleteMutation$data = {
  readonly deleteTodo: {
    readonly __typename: "InternalError";
    readonly category: ErrorCategory;
    readonly code: string;
    readonly message: string;
  } | {
    readonly __typename: "NotFoundError";
    readonly category: ErrorCategory;
    readonly code: string;
    readonly message: string;
  } | {
    readonly __typename: "Success";
    readonly message: string;
    readonly success: boolean;
  } | {
    // This will never be '%other', but we need some
    // value in case none of the concrete values match.
    readonly __typename: "%other";
  };
};
export type TodoItemRelayContainerDeleteMutation = {
  response: TodoItemRelayContainerDeleteMutation$data;
  variables: TodoItemRelayContainerDeleteMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "id"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "message",
  "storageKey": null
},
v2 = [
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "category",
    "storageKey": null
  },
  (v1/*: any*/),
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "code",
    "storageKey": null
  }
],
v3 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "id",
        "variableName": "id"
      }
    ],
    "concreteType": null,
    "kind": "LinkedField",
    "name": "deleteTodo",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "__typename",
        "storageKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": [
          (v1/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "success",
            "storageKey": null
          }
        ],
        "type": "Success",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": (v2/*: any*/),
        "type": "NotFoundError",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": (v2/*: any*/),
        "type": "InternalError",
        "abstractKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoItemRelayContainerDeleteMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "TodoItemRelayContainerDeleteMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "593a8fc4526599508759600b4de91e73",
    "id": null,
    "metadata": {},
    "name": "TodoItemRelayContainerDeleteMutation",
    "operationKind": "mutation",
    "text": "mutation TodoItemRelayContainerDeleteMutation(\n  $id: ID!\n) {\n  deleteTodo(id: $id) {\n    __typename\n    ... on Success {\n      message\n      success\n    }\n    ... on NotFoundError {\n      category\n      message\n      code\n    }\n    ... on InternalError {\n      category\n      message\n      code\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "050dde93c6afb0135a330c759de956c5";

export default node;
