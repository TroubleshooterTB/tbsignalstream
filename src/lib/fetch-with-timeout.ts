/**
 * Fetch with automatic timeout handling
 * Prevents hanging requests that could cause 504 errors
 * 
 * @param url - The URL to fetch
 * @param options - Standard fetch options
 * @param timeoutMs - Timeout in milliseconds (default: 5000)
 * @returns Promise<Response>
 * 
 * @example
 * const response = await fetchWithTimeout('/api/data', { method: 'POST' });
 */
export async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 5000
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if ((error as Error).name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  }
}

/**
 * Fetch with timeout and automatic JSON parsing
 * Handles non-JSON responses gracefully
 * 
 * @param url - The URL to fetch
 * @param options - Standard fetch options
 * @param timeoutMs - Timeout in milliseconds
 * @returns Promise<T> - Parsed JSON response
 */
export async function fetchJsonWithTimeout<T = any>(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 5000
): Promise<T> {
  const response = await fetchWithTimeout(url, options, timeoutMs);
  
  if (!response.ok) {
    // Try to parse error as JSON, fallback to text
    try {
      const error = await response.json();
      throw new Error(error.error || error.message || `HTTP ${response.status}`);
    } catch {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  // Safely parse JSON response
  try {
    return await response.json();
  } catch (error) {
    throw new Error('Invalid JSON response from server');
  }
}
