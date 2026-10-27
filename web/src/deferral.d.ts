/** Types for `deferral.js`. The implementation is plain JavaScript so the gate can execute the same
 *  bytes the bundle ships; see the header of `deferral.js`. */
export declare function deferralKind(reason: unknown): "github" | "ours" | "registry" | "unknown";
export declare function deferralText(reason: unknown): { head: string; body: string };
