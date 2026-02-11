/**
 * @generated SignedSource<<2d41893a5f564319dd031e762857ab0d>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ErrorCategory = "AUTHENTICATION" | "AUTHORIZATION" | "CONFLICT" | "EXTERNAL_SERVICE" | "INTERNAL" | "NOT_FOUND" | "RATE_LIMIT" | "VALIDATION" | "%future added value";
export type TodoListRelayContainerDeleteMutation$variables = {
  id: string;
};
export type TodoListRelayContainerDeleteMutation$data = {
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
export type TodoListRelayContainerDeleteMutation = {
  response: TodoListRelayContainerDeleteMutation$data;
  variables: TodoListRelayContainerDeleteMutation$variables;
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
    "name": "TodoListRelayContainerDeleteMutation",
    "selections": (v3/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "TodoListRelayContainerDeleteMutation",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "0a03544babe7f22824fdf0241d3da8c0",
    "id": null,
    "metadata": {},
    "name": "TodoListRelayContainerDeleteMutation",
    "operationKind": "mutation",
    "text": "mutation TodoListRelayContainerDeleteMutation(\n  $id: ID!\n) {\n  deleteTodo(id: $id) {\n    __typename\n    ... on Success {\n      message\n      success\n    }\n    ... on NotFoundError {\n      category\n      message\n      code\n    }\n    ... on InternalError {\n      category\n      message\n      code\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "553aa970e95083fb89ca5b7616047015";

export default node;
