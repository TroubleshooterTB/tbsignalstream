/**
 * Custom hook for Firestore real-time listeners with automatic cleanup
 * Eliminates duplicate listener setup code across components
 * 
 * @template T - The type of data returned from Firestore
 * @param collectionPath - Firestore collection path (e.g., 'trading_signals')
 * @param queryConstraints - Array of Firestore query constraints
 * @param onData - Callback function when data updates
 * @param options - Optional configuration
 * 
 * @example
 * ```tsx
 * // Before (13 lines):
 * useEffect(() => {
 *   if (!firebaseUser) return;
 *   const q = query(collection(db, 'trading_signals'), where('user_id', '==', firebaseUser.uid));
 *   const unsubscribe = onSnapshot(q, (snapshot) => {
 *     setSignals(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
 *   });
 *   return () => unsubscribe();
 * }, [firebaseUser]);
 * 
 * // After (4 lines):
 * useFirestoreListener<Signal>(
 *   'trading_signals',
 *   [where('user_id', '==', firebaseUser?.uid)],
 *   setSignals,
 *   { enabled: !!firebaseUser }
 * );
 * ```
 */

import { useEffect } from 'react';
import { collection, query, onSnapshot, QueryConstraint } from 'firebase/firestore';
import type { DocumentData } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useAuth } from '@/context/auth-context';

interface UseFirestoreListenerOptions {
  /** Whether the listener is enabled (default: true) */
  enabled?: boolean;
  /** Custom error message prefix */
  errorMessage?: string;
  /** Whether to automatically add user_id to documents */
  includeId?: boolean;
}

export function useFirestoreListener<T = DocumentData>(
  collectionPath: string,
  queryConstraints: QueryConstraint[],
  onData: (data: T[]) => void,
  options: UseFirestoreListenerOptions = {}
) {
  const { firebaseUser } = useAuth();
  const { enabled = true, errorMessage, includeId = true } = options;

  useEffect(() => {
    // Don't set up listener if disabled or no user (for user-scoped data)
    if (!enabled) return;

    const q = query(collection(db, collectionPath), ...queryConstraints);
    
    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        const data = snapshot.docs.map(doc => {
          const docData = doc.data();
          return includeId ? { id: doc.id, ...docData } as T : docData as T;
        });
        onData(data);
      },
      (error) => {
        const prefix = errorMessage || `[${collectionPath}]`;
        console.warn(`${prefix} Listener error:`, error.message);
        // Don't throw - just log and continue
        // This handles permission errors gracefully
      }
    );

    return () => unsubscribe();
  }, [collectionPath, firebaseUser, enabled, errorMessage, includeId, onData, ...queryConstraints]);
}

/**
 * Hook for listening to a single Firestore document
 * 
 * @example
 * ```tsx
 * useFirestoreDocListener<BotConfig>(
 *   'bot_configs',
 *   userId,
 *   (config) => setBotConfig(config)
 * );
 * ```
 */
export function useFirestoreDocListener<T = DocumentData>(
  collectionPath: string,
  documentId: string | null | undefined,
  onData: (data: T | null) => void,
  options: UseFirestoreListenerOptions = {}
) {
  const { enabled = true, errorMessage } = options;

  useEffect(() => {
    if (!enabled || !documentId) return;

    const docRef = doc(db, collectionPath, documentId);
    
    const unsubscribe = onSnapshot(
      docRef,
      (docSnap) => {
        if (docSnap.exists()) {
          onData({ id: docSnap.id, ...docSnap.data() } as T);
        } else {
          onData(null);
        }
      },
      (error) => {
        const prefix = errorMessage || `[${collectionPath}/${documentId}]`;
        console.warn(`${prefix} Listener error:`, error.message);
        onData(null);
      }
    );

    return () => unsubscribe();
  }, [collectionPath, documentId, enabled, errorMessage, onData]);
}

// Re-export doc for convenience
import { doc } from 'firebase/firestore';
export { doc };
