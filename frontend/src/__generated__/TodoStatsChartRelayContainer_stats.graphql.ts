/**
 * @generated SignedSource<<53f0527b5cc22b99861a453b5b2ce1e0>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
export type PriorityEnum = "HIGH" | "LOW" | "MEDIUM" | "%future added value";
import { FragmentRefs } from "relay-runtime";
export type TodoStatsChartRelayContainer_stats$data = {
  readonly priorityStats: ReadonlyArray<{
    readonly count: number;
    readonly priority: PriorityEnum;
  }>;
  readonly " $fragmentType": "TodoStatsChartRelayContainer_stats";
};
export type TodoStatsChartRelayContainer_stats$key = {
  readonly " $data"?: TodoStatsChartRelayContainer_stats$data;
  readonly " $fragmentSpreads": FragmentRefs<"TodoStatsChartRelayContainer_stats">;
};

const node: ReaderFragment = {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "TodoStatsChartRelayContainer_stats",
  "selections": [
    {
      "alias": null,
      "args": null,
      "concreteType": "PriorityStatsType",
      "kind": "LinkedField",
      "name": "priorityStats",
      "plural": true,
      "selections": [
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
          "name": "count",
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "Query",
  "abstractKey": null
};

(node as any).hash = "f049360e2ba7c0ecbeffab8353c2b854";

export default node;
