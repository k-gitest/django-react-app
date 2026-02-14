/**
 * @generated SignedSource<<ea403ce6b71e59fc844036653f0a508f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ErrorCategory = "AUTHENTICATION" | "AUTHORIZATION" | "CONFLICT" | "EXTERNAL_SERVICE" | "INTERNAL" | "NOT_FOUND" | "RATE_LIMIT" | "VALIDATION" | "%future added value";
export type TodoItemRelayContainerDeleteMutation$variables = {
  connections: ReadonlyArray<string>;
  id: string;
};
export type TodoItemRelayContainerDeleteMutation$data = {
  readonly deleteTodo: {
    readonly __typename: "DeleteTodoPayload";
    readonly deletedTodoId: string;
    readonly message: string;
  } | {
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
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "connections"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "id"
},
v2 = [
  {
    "kind": "Variable",
    "name": "id",
    "variableName": "id"
  }
],
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "__typename",
  "storageKey": null
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "message",
  "storageKey": null
},
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "deletedTodoId",
  "storageKey": null
},
v6 = [
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "category",
    "storageKey": null
  },
  (v4/*: any*/),
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "code",
    "storageKey": null
  }
],
v7 = {
  "kind": "InlineFragment",
  "selections": (v6/*: any*/),
  "type": "NotFoundError",
  "abstractKey": null
},
v8 = {
  "kind": "InlineFragment",
  "selections": (v6/*: any*/),
  "type": "InternalError",
  "abstractKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoItemRelayContainerDeleteMutation",
    "selections": [
      {
        "alias": null,
        "args": (v2/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "deleteTodo",
        "plural": false,
        "selections": [
          (v3/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v4/*: any*/),
              (v5/*: any*/)
            ],
            "type": "DeleteTodoPayload",
            "abstractKey": null
          },
          (v7/*: any*/),
          (v8/*: any*/)
        ],
        "storageKey": null
      }
    ],
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "TodoItemRelayContainerDeleteMutation",
    "selections": [
      {
        "alias": null,
        "args": (v2/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "deleteTodo",
        "plural": false,
        "selections": [
          (v3/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v4/*: any*/),
              (v5/*: any*/),
              {
                "alias": null,
                "args": null,
                "filters": null,
                "handle": "deleteEdge",
                "key": "",
                "kind": "ScalarHandle",
                "name": "deletedTodoId",
                "handleArgs": [
                  {
                    "kind": "Variable",
                    "name": "connections",
                    "variableName": "connections"
                  }
                ]
              }
            ],
            "type": "DeleteTodoPayload",
            "abstractKey": null
          },
          (v7/*: any*/),
          (v8/*: any*/)
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "2d7e660bd2a771f9f2ce999ba62c4d26",
    "id": null,
    "metadata": {},
    "name": "TodoItemRelayContainerDeleteMutation",
    "operationKind": "mutation",
    "text": "mutation TodoItemRelayContainerDeleteMutation(\n  $id: ID!\n) {\n  deleteTodo(id: $id) {\n    __typename\n    ... on DeleteTodoPayload {\n      message\n      deletedTodoId\n    }\n    ... on NotFoundError {\n      category\n      message\n      code\n    }\n    ... on InternalError {\n      category\n      message\n      code\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "df1fa75483e4ff79e9f36b5c68157abe";

export default node;
