import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useFirestoreListener, useFirestoreDocListener } from '../use-firestore-listener';
import { collection, query, where, onSnapshot, doc } from 'firebase/firestore';
import { useAuth } from '@/context/auth-context';

// Mock Firebase
vi.mock('firebase/firestore', () => ({
  collection: vi.fn(),
  query: vi.fn(),
  where: vi.fn(),
  orderBy: vi.fn(),
  limit: vi.fn(),
  onSnapshot: vi.fn(),
  doc: vi.fn(),
  getFirestore: vi.fn(),
}));

// Mock auth context
vi.mock('@/context/auth-context', () => ({
  useAuth: vi.fn(),
}));

// Mock db
vi.mock('@/lib/firebase', () => ({
  db: {},
}));

describe('useFirestoreListener', () => {
  let mockUnsubscribe: () => void;
  
  beforeEach(() => {
    mockUnsubscribe = vi.fn();
    vi.mocked(useAuth).mockReturnValue({
      firebaseUser: { uid: 'test-user-123' },
    } as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should set up Firestore listener on mount', () => {
    const mockOnData = vi.fn();
    const mockQueryConstraints = [where('user_id', '==', 'test-user')];
    
    vi.mocked(onSnapshot).mockReturnValue(mockUnsubscribe);
    vi.mocked(collection).mockReturnValue({} as any);
    vi.mocked(query).mockReturnValue({} as any);

    const { unmount } = renderHook(() =>
      useFirestoreListener(
        'test_collection',
        mockQueryConstraints,
        mockOnData
      )
    );

    expect(collection).toHaveBeenCalled();
    expect(query).toHaveBeenCalled();
    expect(onSnapshot).toHaveBeenCalled();

    unmount();
    expect(mockUnsubscribe).toHaveBeenCalled();
  });

  it('should call onData with fetched documents', async () => {
    const mockOnData = vi.fn();
    const mockDocs = [
      { id: 'doc1', data: () => ({ name: 'Test 1' }) },
      { id: 'doc2', data: () => ({ name: 'Test 2' }) },
    ];

    vi.mocked(onSnapshot).mockImplementation((q, callback: any) => {
      callback({
        docs: mockDocs,
        empty: false,
      });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData)
    );

    expect(mockOnData).toHaveBeenCalledWith([
      { id: 'doc1', name: 'Test 1' },
      { id: 'doc2', name: 'Test 2' },
    ]);
  });

  it('should handle empty snapshot', async () => {
    const mockOnData = vi.fn();

    vi.mocked(onSnapshot).mockImplementation((q, callback: any) => {
      callback({
        docs: [],
        empty: true,
      });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData)
    );

    expect(mockOnData).toHaveBeenCalledWith([]);
  });

  it('should not set up listener when enabled is false', () => {
    const mockOnData = vi.fn();

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData, {
        enabled: false,
      })
    );

    expect(onSnapshot).not.toHaveBeenCalled();
  });

  it('should handle errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const mockOnData = vi.fn();
    const testError = new Error('Firestore error');

    vi.mocked(onSnapshot).mockImplementation((q, callback: any, errorHandler: any) => {
      errorHandler(testError);
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData, {
        errorMessage: '[TestCollection]',
      })
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      '[TestCollection] Error listening to Firestore:',
      testError
    );

    consoleSpy.mockRestore();
  });

  it('should include document ID when includeId is true', async () => {
    const mockOnData = vi.fn();
    const mockDocs = [
      { id: 'doc1', data: () => ({ name: 'Test' }) },
    ];

    vi.mocked(onSnapshot).mockImplementation((q, callback: any) => {
      callback({ docs: mockDocs, empty: false });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData, {
        includeId: true,
      })
    );

    expect(mockOnData).toHaveBeenCalledWith([
      { id: 'doc1', name: 'Test' },
    ]);
  });

  it('should not include document ID when includeId is false', async () => {
    const mockOnData = vi.fn();
    const mockDocs = [
      { id: 'doc1', data: () => ({ name: 'Test' }) },
    ];

    vi.mocked(onSnapshot).mockImplementation((q, callback: any) => {
      callback({ docs: mockDocs, empty: false });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreListener('test_collection', [], mockOnData, {
        includeId: false,
      })
    );

    expect(mockOnData).toHaveBeenCalledWith([
      { name: 'Test' },
    ]);
  });
});

describe('useFirestoreDocListener', () => {
  let mockUnsubscribe: () => void;

  beforeEach(() => {
    mockUnsubscribe = vi.fn();
    vi.mocked(useAuth).mockReturnValue({
      firebaseUser: { uid: 'test-user-123' },
    } as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should set up document listener on mount', () => {
    const mockOnData = vi.fn();
    
    vi.mocked(onSnapshot).mockReturnValue(mockUnsubscribe);
    vi.mocked(doc).mockReturnValue({} as any);

    const { unmount } = renderHook(() =>
      useFirestoreDocListener('test_collection', 'doc123', mockOnData)
    );

    expect(doc).toHaveBeenCalled();
    expect(onSnapshot).toHaveBeenCalled();

    unmount();
    expect(mockUnsubscribe).toHaveBeenCalled();
  });

  it('should call onData with document data when it exists', async () => {
    const mockOnData = vi.fn();
    const mockDocData = { name: 'Test Document', value: 42 };

    vi.mocked(onSnapshot).mockImplementation((docRef, callback: any) => {
      callback({
        exists: () => true,
        data: () => mockDocData,
      });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreDocListener('test_collection', 'doc123', mockOnData)
    );

    expect(mockOnData).toHaveBeenCalledWith(mockDocData);
  });

  it('should call onData with null when document does not exist', async () => {
    const mockOnData = vi.fn();

    vi.mocked(onSnapshot).mockImplementation((docRef, callback: any) => {
      callback({
        exists: () => false,
        data: () => undefined,
      });
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreDocListener('test_collection', 'doc123', mockOnData)
    );

    expect(mockOnData).toHaveBeenCalledWith(null);
  });

  it('should not set up listener when enabled is false', () => {
    const mockOnData = vi.fn();

    renderHook(() =>
      useFirestoreDocListener('test_collection', 'doc123', mockOnData, {
        enabled: false,
      })
    );

    expect(onSnapshot).not.toHaveBeenCalled();
  });

  it('should handle errors in document listener', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const mockOnData = vi.fn();
    const testError = new Error('Document read error');

    vi.mocked(onSnapshot).mockImplementation((docRef, callback: any, errorHandler: any) => {
      errorHandler(testError);
      return mockUnsubscribe as any;
    });

    renderHook(() =>
      useFirestoreDocListener('test_collection', 'doc123', mockOnData, {
        errorMessage: '[TestDoc]',
      })
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      '[TestDoc] Error listening to Firestore document:',
      testError
    );

    consoleSpy.mockRestore();
  });
});
