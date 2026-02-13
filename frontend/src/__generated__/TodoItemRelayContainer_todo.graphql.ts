/**
 * @generated SignedSource<<643f957d48f2777009b7ab4c5a2a6626>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
import { FragmentRefs } from "relay-runtime";
export type TodoItemRelayContainer_todo$data = {
  readonly id: string;
  readonly priority: PriorityEnum;
  readonly progress: number;
  readonly todoTitle: string;
  readonly updatedAt: any;
  readonly " $fragmentSpreads": FragmentRefs<"TodoEditModalRelayContainer_todo">;
  readonly " $fragmentType": "TodoItemRelayContainer_todo";
};
export type TodoItemRelayContainer_todo$key = {
  readonly " $data"?: TodoItemRelayContainer_todo$data;
  readonly " $fragmentSpreads": FragmentRefs<"TodoItemRelayContainer_todo">;
};

const node: ReaderFragment = {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "TodoItemRelayContainer_todo",
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
    },
    {
      "args": null,
      "kind": "FragmentSpread",
      "name": "TodoEditModalRelayContainer_todo"
    }
  ],
  "type": "TodoType",
  "abstractKey": null
};

(node as any).hash = "55a7a0c0691fe4f62d192419edabd3af";

export default node;
