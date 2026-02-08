/**
 * @generated SignedSource<<7e35a873d9f898599ffda93d02e0f634>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type ErrorCategory = "AUTHENTICATION" | "AUTHORIZATION" | "CONFLICT" | "EXTERNAL_SERVICE" | "INTERNAL" | "NOT_FOUND" | "RATE_LIMIT" | "VALIDATION" | "%future added value";
export type RegisterInput = {
  email: string;
  firstName?: string | null | undefined;
  lastName?: string | null | undefined;
  password: string;
  passwordConfirm: string;
};
export type AuthFormRelayContainerRegisterMutation$variables = {
  input: RegisterInput;
};
export type AuthFormRelayContainerRegisterMutation$data = {
  readonly register: {
    readonly __typename: "AuthPayload";
    readonly message: string;
    readonly user: {
      readonly dateJoined: any;
      readonly email: string;
      readonly firstName: string;
      readonly id: number;
      readonly isStaff: boolean;
      readonly lastName: string;
    };
  } | {
    readonly __typename: "ConflictError";
    readonly category: ErrorCategory;
    readonly code: string;
    readonly conflictingField: string | null | undefined;
    readonly message: string;
  } | {
    readonly __typename: "InternalError";
    readonly category: ErrorCategory;
    readonly code: string;
    readonly message: string;
  } | {
    readonly __typename: "ValidationError";
    readonly category: ErrorCategory;
    readonly code: string;
    readonly field: string | null | undefined;
    readonly message: string;
  } | {
    // This will never be '%other', but we need some
    // value in case none of the concrete values match.
    readonly __typename: "%other";
  };
};
export type AuthFormRelayContainerRegisterMutation = {
  response: AuthFormRelayContainerRegisterMutation$data;
  variables: AuthFormRelayContainerRegisterMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "input"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "message",
  "storageKey": null
},
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "category",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "code",
  "storageKey": null
},
v4 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "input",
        "variableName": "input"
      }
    ],
    "concreteType": null,
    "kind": "LinkedField",
    "name": "register",
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
            "concreteType": "UserType",
            "kind": "LinkedField",
            "name": "user",
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
                "name": "email",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "firstName",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "lastName",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "isStaff",
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "kind": "ScalarField",
                "name": "dateJoined",
                "storageKey": null
              }
            ],
            "storageKey": null
          },
          (v1/*: any*/)
        ],
        "type": "AuthPayload",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": [
          (v2/*: any*/),
          (v1/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "field",
            "storageKey": null
          },
          (v3/*: any*/)
        ],
        "type": "ValidationError",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": [
          (v2/*: any*/),
          (v1/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "conflictingField",
            "storageKey": null
          },
          (v3/*: any*/)
        ],
        "type": "ConflictError",
        "abstractKey": null
      },
      {
        "kind": "InlineFragment",
        "selections": [
          (v2/*: any*/),
          (v1/*: any*/),
          (v3/*: any*/)
        ],
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
    "name": "AuthFormRelayContainerRegisterMutation",
    "selections": (v4/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "AuthFormRelayContainerRegisterMutation",
    "selections": (v4/*: any*/)
  },
  "params": {
    "cacheID": "a94f5b7574394ca37e39f043a0f4883f",
    "id": null,
    "metadata": {},
    "name": "AuthFormRelayContainerRegisterMutation",
    "operationKind": "mutation",
    "text": "mutation AuthFormRelayContainerRegisterMutation(\n  $input: RegisterInput!\n) {\n  register(input: $input) {\n    __typename\n    ... on AuthPayload {\n      user {\n        id\n        email\n        firstName\n        lastName\n        isStaff\n        dateJoined\n      }\n      message\n    }\n    ... on ValidationError {\n      category\n      message\n      field\n      code\n    }\n    ... on ConflictError {\n      category\n      message\n      conflictingField\n      code\n    }\n    ... on InternalError {\n      category\n      message\n      code\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "0787640d5071575cdb794d138e361734";

export default node;
