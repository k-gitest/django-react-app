/**
 * @generated SignedSource<<cdc18f9d00d2f03b672e5b7ed8894e07>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type useAuthUserRelayQuery$variables = Record<PropertyKey, never>;
export type useAuthUserRelayQuery$data = {
  readonly me: {
    readonly __typename: "UserType";
    readonly email: string;
    readonly firstName: string;
    readonly id: number;
    readonly isStaff: boolean;
    readonly lastName: string;
  } | null | undefined;
};
export type useAuthUserRelayQuery = {
  response: useAuthUserRelayQuery$data;
  variables: useAuthUserRelayQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "UserType",
    "kind": "LinkedField",
    "name": "me",
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
    "name": "useAuthUserRelayQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "useAuthUserRelayQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "76c1590a5fba400fb20e89af8c689f06",
    "id": null,
    "metadata": {},
    "name": "useAuthUserRelayQuery",
    "operationKind": "query",
    "text": "query useAuthUserRelayQuery {\n  me {\n    __typename\n    id\n    email\n    firstName\n    lastName\n    isStaff\n  }\n}\n"
  }
};
})();

(node as any).hash = "80135a5c6a33784fb73fdb9ecd765f4f";

export default node;
