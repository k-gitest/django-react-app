/**
 * @generated SignedSource<<5dfa126ad6a4e14f5fa000a9f15cbeed>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
import { FragmentRefs } from "relay-runtime";
export type TodoEditModalRelayContainer_todo$data = {
  readonly id: string;
  readonly priority: PriorityEnum;
  readonly progress: number;
  readonly todoTitle: string;
  readonly " $fragmentType": "TodoEditModalRelayContainer_todo";
};
export type TodoEditModalRelayContainer_todo$key = {
  readonly " $data"?: TodoEditModalRelayContainer_todo$data;
  readonly " $fragmentSpreads": FragmentRefs<"TodoEditModalRelayContainer_todo">;
};

const node: ReaderFragment = {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "TodoEditModalRelayContainer_todo",
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
    }
  ],
  "type": "TodoType",
  "abstractKey": null
};

(node as any).hash = "ee132d068776cb51dea9ddd355d6d4ac";

export default node;
