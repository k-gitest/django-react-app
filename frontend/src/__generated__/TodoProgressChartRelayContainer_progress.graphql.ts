/**
 * @generated SignedSource<<388856a55de559273986f76a6ffcc3dc>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type TodoProgressChartRelayContainer_progress$data = {
  readonly progressStats: {
    readonly range020: number;
    readonly range2140: number;
    readonly range4160: number;
    readonly range6180: number;
    readonly range81100: number;
  };
  readonly " $fragmentType": "TodoProgressChartRelayContainer_progress";
};
export type TodoProgressChartRelayContainer_progress$key = {
  readonly " $data"?: TodoProgressChartRelayContainer_progress$data;
  readonly " $fragmentSpreads": FragmentRefs<"TodoProgressChartRelayContainer_progress">;
};

const node: ReaderFragment = {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "TodoProgressChartRelayContainer_progress",
  "selections": [
    {
      "alias": null,
      "args": null,
      "concreteType": "ProgressStatsType",
      "kind": "LinkedField",
      "name": "progressStats",
      "plural": false,
      "selections": [
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "range020",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "range2140",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "range4160",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "range6180",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "range81100",
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "Query",
  "abstractKey": null
};

(node as any).hash = "6196466573af311bedbcc9039ca94676";

export default node;
