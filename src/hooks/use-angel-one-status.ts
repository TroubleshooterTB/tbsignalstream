/**
 * Angel One Connection Status Hook
 * Checks if the user has valid Angel One credentials
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/auth-context';
import { db } from '@/lib/firebase';
import { doc, getDoc } from 'firebase/firestore';

export interface AngelOneStatus {
  isConnected: boolean;
  isLoading: boolean;
  lastConnected?: Date;
  clientCode?: string;
}

export function useAngelOneStatus(): AngelOneStatus {
  const { firebaseUser } = useAuth();
  const [status, setStatus] = useState<AngelOneStatus>({
    isConnected: false,
    isLoading: true,
  });

  useEffect(() => {
    if (!firebaseUser) {
      setStatus({ isConnected: false, isLoading: false });
      return;
    }

    const checkConnection = async () => {
      try {
        const credDoc = await getDoc(doc(db, 'angel_one_credentials', firebaseUser.uid));
        
        if (credDoc.exists()) {
          const data = credDoc.data();
          setStatus({
            isConnected: !!(data.jwt_token && data.feed_token),
            isLoading: false,
            lastConnected: data.updated_at?.toDate(),
            clientCode: data.client_code,
          });
        } else {
          setStatus({ isConnected: false, isLoading: false });
        }
      } catch (error) {
        console.error('Failed to check Angel One connection:', error);
        setStatus({ isConnected: false, isLoading: false });
      }
    };

    checkConnection();
  }, [firebaseUser]);

  return status;
}
