/**
 * @generated SignedSource<<6bb76405bcfbf2237cf6f092606f49fe>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
export type TodoUpdateInput = {
  priority?: PriorityEnum | null | undefined;
  progress?: number | null | undefined;
  todoTitle?: string | null | undefined;
};
export type TodoEditModalRelayContainerUpdateMutation$variables = {
  id: string;
  input: TodoUpdateInput;
};
export type TodoEditModalRelayContainerUpdateMutation$data = {
  readonly updateTodo: {
    readonly __typename: "TodoType";
    readonly id: string;
    readonly priority: PriorityEnum;
    readonly progress: number;
    readonly todoTitle: string;
  } | {
    readonly __typename: "ValidationError";
    readonly message: string;
  } | {
    // This will never be '%other', but we need some
    // value in case none of the concrete values match.
    readonly __typename: "%other";
  };
};
export type TodoEditModalRelayContainerUpdateMutation = {
  response: TodoEditModalRelayContainerUpdateMutation$data;
  variables: TodoEditModalRelayContainerUpdateMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "id"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "input"
  }
],
v1 = [
  {
    "kind": "Variable",
    "name": "id",
    "variableName": "id"
  },
  {
    "kind": "Variable",
    "name": "input",
    "variableName": "input"
  }
],
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "__typename",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v4 = {
  "kind": "InlineFragment",
  "selections": [
    (v3/*: any*/),
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
    }
  ],
  "type": "TodoType",
  "abstractKey": null
},
v5 = {
  "kind": "InlineFragment",
  "selections": [
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "message",
      "storageKey": null
    }
  ],
  "type": "ValidationError",
  "abstractKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoEditModalRelayContainerUpdateMutation",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "updateTodo",
        "plural": false,
        "selections": [
          (v2/*: any*/),
          (v4/*: any*/),
          (v5/*: any*/)
        ],
        "storageKey": null
      }
    ],
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "TodoEditModalRelayContainerUpdateMutation",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "updateTodo",
        "plural": false,
        "selections": [
          (v2/*: any*/),
          (v4/*: any*/),
          (v5/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v3/*: any*/)
            ],
            "type": "Node",
            "abstractKey": "__isNode"
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "36819f5be6dd49be77cce0104030d396",
    "id": null,
    "metadata": {},
    "name": "TodoEditModalRelayContainerUpdateMutation",
    "operationKind": "mutation",
    "text": "mutation TodoEditModalRelayContainerUpdateMutation(\n  $id: ID!\n  $input: TodoUpdateInput!\n) {\n  updateTodo(id: $id, input: $input) {\n    __typename\n    ... on TodoType {\n      id\n      todoTitle\n      priority\n      progress\n    }\n    ... on ValidationError {\n      message\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "07b54e3d6b5d7fb8f0f787dd25b4ade9";

export default node;
