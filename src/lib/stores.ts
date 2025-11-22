import { atom } from 'nanostores';
import type { User } from 'firebase/auth';

/**
 * A nano store that holds the authenticated Firebase user object.
 * It will be:
 *   - `undefined` initially, while the auth state is being checked.
 *   - `null` if the user is not logged in.
 *   - A `User` object if the user is logged in.
 */
export const user = atom<User | null | undefined>(undefined);
