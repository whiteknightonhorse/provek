export const RPC_URL: string;
export function bradburyChain<T extends { id: number; rpcUrls?: { default?: { http?: readonly string[] } } }>(base: T): T;
