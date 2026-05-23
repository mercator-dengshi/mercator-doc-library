import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'editor' | 'viewer';
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null; // Store in memory only
  login: (user: User, accessToken: string) => void;
  logout: () => void;
  getAccessToken: () => string | null;
}

// Use sessionStorage for better security (cleared when browser closes)
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      login: (user, accessToken) => {
        set({ 
          user, 
          isAuthenticated: true,
          accessToken 
        });
      },
      logout: () => {
        set({ 
          user: null, 
          isAuthenticated: false,
          accessToken: null 
        });
      },
      getAccessToken: () => get().accessToken,
    }),
    {
      name: 'auth-storage', // unique name for storage key
      storage: createJSONStorage(() => sessionStorage), // use sessionStorage instead of localStorage
      // Persist both user and token for session continuity
      // Token will be cleared when browser tab closes (sessionStorage behavior)
    }
  )
);
