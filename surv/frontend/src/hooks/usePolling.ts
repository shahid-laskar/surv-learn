import { useQuery, type UseQueryOptions } from '@tanstack/react-query'

export function usePolling<T>(
  key:        unknown[],
  fn:         () => Promise<T>,
  intervalMs: number = 15_000,
  options?:   Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn' | 'refetchInterval'>
) {
  return useQuery<T>({
    queryKey:       key,
    queryFn:        fn,
    refetchInterval: intervalMs,
    // Make polling self-healing after temporary network failures.
    // This prevents "stuck" UI like motion alerts staying active.
    refetchOnReconnect:   true,
    refetchOnWindowFocus: true,
    retry:                3,
    ...options,
  })
}
