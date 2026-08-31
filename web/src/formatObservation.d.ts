/** Types for `formatObservation.js`. The implementation is plain JavaScript so the gate can run
 *  the same bytes the bundle ships; see the header of `formatObservation.js` for why. */
export declare const SHARE_OBSERVATION_KEYS: string[];
export declare function formatObservationValue(key: string, value: number | boolean): string;
