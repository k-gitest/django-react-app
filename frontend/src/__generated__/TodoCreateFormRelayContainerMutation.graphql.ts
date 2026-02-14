/**
 * @generated SignedSource<<6c20b9eb276a7a79609efbfb73d4bf05>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
export type TodoCreateInput = {
  priority?: PriorityEnum;
  progress?: number;
  todoTitle: string;
};
export type TodoCreateFormRelayContainerMutation$variables = {
  connections: ReadonlyArray<string>;
  input: TodoCreateInput;
};
export type TodoCreateFormRelayContainerMutation$data = {
  readonly createTodo: {
    readonly __typename: "CreateTodoPayload";
    readonly todoEdge: {
      readonly node: {
        readonly createdAt: any;
        readonly id: string;
        readonly priority: PriorityEnum;
        readonly progress: number;
        readonly todoTitle: string;
        readonly updatedAt: any;
      };
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
export type TodoCreateFormRelayContainerMutation = {
  response: TodoCreateFormRelayContainerMutation$data;
  variables: TodoCreateFormRelayContainerMutation$variables;
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
  "name": "input"
},
v2 = [
  {
    "kind": "Variable",
    "name": "input",
    "variableName": "input"
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
  "concreteType": "TodoEdge",
  "kind": "LinkedField",
  "name": "todoEdge",
  "plural": false,
  "selections": [
    {
      "alias": null,
      "args": null,
      "concreteType": "TodoType",
      "kind": "LinkedField",
      "name": "node",
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
          "name": "progress",
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
          "name": "createdAt",
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
  "storageKey": null
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
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "TodoCreateFormRelayContainerMutation",
    "selections": [
      {
        "alias": null,
        "args": (v2/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "createTodo",
        "plural": false,
        "selections": [
          (v3/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v4/*: any*/)
            ],
            "type": "CreateTodoPayload",
            "abstractKey": null
          },
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
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "TodoCreateFormRelayContainerMutation",
    "selections": [
      {
        "alias": null,
        "args": (v2/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "createTodo",
        "plural": false,
        "selections": [
          (v3/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v4/*: any*/),
              {
                "alias": null,
                "args": null,
                "filters": null,
                "handle": "prependEdge",
                "key": "",
                "kind": "LinkedHandle",
                "name": "todoEdge",
                "handleArgs": [
                  {
                    "kind": "Variable",
                    "name": "connections",
                    "variableName": "connections"
                  }
                ]
              }
            ],
            "type": "CreateTodoPayload",
            "abstractKey": null
          },
          (v5/*: any*/)
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "d5d508a7732176baee0f2335368561ab",
    "id": null,
    "metadata": {},
    "name": "TodoCreateFormRelayContainerMutation",
    "operationKind": "mutation",
    "text": "mutation TodoCreateFormRelayContainerMutation(\n  $input: TodoCreateInput!\n) {\n  createTodo(input: $input) {\n    __typename\n    ... on CreateTodoPayload {\n      todoEdge {\n        node {\n          id\n          todoTitle\n          progress\n          priority\n          createdAt\n          updatedAt\n        }\n      }\n    }\n    ... on ValidationError {\n      message\n      field\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "b6f4ddcf44260905f5f2a4b050a20fef";

export default node;
