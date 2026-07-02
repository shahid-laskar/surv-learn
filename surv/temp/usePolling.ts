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
    ...options,
  })
}
