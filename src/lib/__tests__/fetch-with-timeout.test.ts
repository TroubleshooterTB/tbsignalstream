import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchWithTimeout, fetchJsonWithTimeout } from '../fetch-with-timeout';

describe('fetchWithTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should successfully fetch data within timeout', async () => {
    const mockResponse = new Response('test data', { status: 200 });
    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    const promise = fetchWithTimeout('https://api.example.com/data', {}, 5000);
    
    // Immediately resolve (no timeout)
    const result = await promise;

    expect(result).toBe(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.com/data',
      expect.objectContaining({
        signal: expect.any(AbortSignal),
      })
    );
  });

  it('should throw timeout error when request takes too long', async () => {
    // Mock a fetch that never resolves
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 10000))
    );

    const promise = fetchWithTimeout('https://api.example.com/slow', {}, 1000);

    // Advance timers to trigger timeout
    vi.advanceTimersByTime(1000);

    await expect(promise).rejects.toThrow('Request timeout after 1000ms');
  });

  it('should abort request on timeout', async () => {
    const abortSpy = vi.spyOn(AbortController.prototype, 'abort');
    
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 10000))
    );

    const promise = fetchWithTimeout('https://api.example.com/slow', {}, 1000);
    
    vi.advanceTimersByTime(1000);

    await expect(promise).rejects.toThrow();
    expect(abortSpy).toHaveBeenCalled();
  });

  it('should pass custom options to fetch', async () => {
    const mockResponse = new Response('data', { status: 200 });
    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    const customOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: 'data' }),
    };

    await fetchWithTimeout('https://api.example.com/data', customOptions, 5000);

    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.com/data',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test: 'data' }),
        signal: expect.any(AbortSignal),
      })
    );
  });
});

describe('fetchJsonWithTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should successfully fetch and parse JSON data', async () => {
    const mockData = { success: true, value: 42 };
    const mockResponse = new Response(JSON.stringify(mockData), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    const result = await fetchJsonWithTimeout<typeof mockData>(
      'https://api.example.com/json',
      {},
      5000
    );

    expect(result).toEqual(mockData);
  });

  it('should throw error for non-OK response', async () => {
    const mockResponse = new Response('Not Found', { status: 404 });
    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    await expect(
      fetchJsonWithTimeout('https://api.example.com/missing', {}, 5000)
    ).rejects.toThrow('HTTP error! status: 404');
  });

  it('should throw error for invalid JSON', async () => {
    const mockResponse = new Response('invalid json{', { status: 200 });
    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    await expect(
      fetchJsonWithTimeout('https://api.example.com/bad-json', {}, 5000)
    ).rejects.toThrow();
  });

  it('should handle timeout in fetchJsonWithTimeout', async () => {
    global.fetch = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 10000))
    );

    const promise = fetchJsonWithTimeout('https://api.example.com/slow', {}, 1000);
    
    vi.advanceTimersByTime(1000);

    await expect(promise).rejects.toThrow('Request timeout after 1000ms');
  });
});
