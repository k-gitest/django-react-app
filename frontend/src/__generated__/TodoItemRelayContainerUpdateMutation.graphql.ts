/**
 * @generated SignedSource<<368823791f39af08d212ce950510e85c>>
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
export type TodoItemRelayContainerUpdateMutation$variables = {
  id: string;
  input: TodoUpdateInput;
};
export type TodoItemRelayContainerUpdateMutation$data = {
  readonly updateTodo: {
    readonly __typename: "UpdateTodoPayload";
    readonly todo: {
      readonly id: string;
      readonly priority: PriorityEnum;
      readonly progress: number;
      readonly todoTitle: string;
      readonly updatedAt: any;
    };
  } | {
    readonly __typename: "ValidationError";
    readonly field: string | null | undefined;
    readonly message: string;
  } | {
    // This will never be '%other', but we need some
    // value in case none of the concrete values match.
    readonly __typename: "%other";
  };
};
export type TodoItemRelayContainerUpdateMutation = {
  response: TodoItemRelayContainerUpdateMutation$data;
  variables: TodoItemRelayContainerUpdateMutation$variables;
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
    "alias": null,
    "args": [
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
    "concreteType": null,
    "kind": "LinkedField",
    "name": "updateTodo",
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
          {
            "alias": null,
            "args": null,
            "concreteType": "TodoType",
            "kind": "LinkedField",
            "name": "todo",
            "plural": false,
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
        ],
        "type": "UpdateTodoPayload",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "message",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "field",
            "storageKey": null
          }
        ],
        "type": "ValidationError",
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
    "name": "TodoItemRelayContainerUpdateMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "TodoItemRelayContainerUpdateMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "5b985a0d3ddae2d32c88ffb9826ffc0b",
    "id": null,
    "metadata": {},
    "name": "TodoItemRelayContainerUpdateMutation",
    "operationKind": "mutation",
    "text": "mutation TodoItemRelayContainerUpdateMutation(\n  $id: ID!\n  $input: TodoUpdateInput!\n) {\n  updateTodo(id: $id, input: $input) {\n    __typename\n    ... on UpdateTodoPayload {\n      todo {\n        id\n        todoTitle\n        priority\n        progress\n        updatedAt\n      }\n    }\n    ... on ValidationError {\n      message\n      field\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "ff70178581a8197866085b16df06ae0b";

export default node;
