import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

interface User {
  id: string;
  email: string;
  phone: string | null;
  display_name: string;
  created_at: string;
  friends_count: number;
  posts_count: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('auth_token');
      if (storedToken) {
        setToken(storedToken);
        // Verify token and get user
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${storedToken}`,
          },
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          // Token invalid, clear it
          await AsyncStorage.removeItem('auth_token');
          setToken(null);
        }
      }
    } catch (error) {
      console.error('Error loading auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      let message = `Login failed (${response.status})`;
      try {
        const body = await response.json();
        const detail = body?.detail;
        if (typeof detail === 'string') message = detail;
        else if (Array.isArray(detail) && detail.length) message = detail.map((e: { msg?: string }) => e?.msg || JSON.stringify(e)).join('. ');
        else if (detail?.message) message = detail.message;
      } catch {
        try {
          const text = await response.text();
          if (text) message = text.slice(0, 200);
        } catch {}
      }
      throw new Error(message);
    }

    const data = await response.json();
    if (!data?.access_token || !data?.user) {
      throw new Error('Invalid response from server');
    }
    await AsyncStorage.setItem('auth_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const register = async (email: string, password: string, displayName: string, phone?: string) => {
    const url = `${API_URL}/api/auth/register`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
        phone: phone || null,
      }),
    });

    if (!response.ok) {
      let message = `Registration failed (${response.status})`;
      try {
        const body = await response.json();
        const detail = body?.detail;
        if (typeof detail === 'string') message = detail;
        else if (Array.isArray(detail) && detail.length) message = detail.map((e: { msg?: string }) => e?.msg || JSON.stringify(e)).join('. ');
        else if (detail?.message) message = detail.message;
      } catch {
        try {
          const text = await response.text();
          if (text) message = text.slice(0, 200);
        } catch {}
      }
      throw new Error(message);
    }

    const data = await response.json();
    if (!data?.access_token || !data?.user) {
      throw new Error('Invalid response from server');
    }
    await AsyncStorage.setItem('auth_token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = async () => {
    await AsyncStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
  };

  const refreshUser = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, updateUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
