import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface InviteInfo {
  invite_code: string;
  user_id: string;
  display_name: string;
  posts_count: number;
  friends_count: number;
  is_already_friend: boolean;
  is_self: boolean;
  request_pending: boolean;
}

export default function InviteScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { code } = useLocalSearchParams<{ code: string }>();
  const { token, user, refreshUser } = useAuth();
  
  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (code && token) {
      fetchInviteInfo();
    }
  }, [code, token]);

  const fetchInviteInfo = async () => {
    if (!code || !token) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/invite/${code}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setInviteInfo(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Invalid invite link');
      }
    } catch (err) {
      setError('Failed to load invite information');
    } finally {
      setLoading(false);
    }
  };

  const acceptInvite = async () => {
    if (!code || !token) return;
    
    setAccepting(true);
    try {
      const response = await fetch(`${API_URL}/api/invite/${code}/accept`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      const data = await response.json();
      
      if (response.ok) {
        await refreshUser();
        Alert.alert('Success!', data.message, [
          { text: 'OK', onPress: () => router.replace('/(tabs)') }
        ]);
      } else {
        Alert.alert('Error', data.detail || 'Failed to accept invite');
      }
    } catch (err) {
      Alert.alert('Error', 'Something went wrong');
    } finally {
      setAccepting(false);
    }
  };

  const goBack = () => {
    router.replace('/(tabs)');
  };

  if (!token) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.content}>
          <Ionicons name="link" size={64} color="#CCC" />
          <Text style={styles.title}>Sign In Required</Text>
          <Text style={styles.subtitle}>
            You need to sign in to accept this invite
          </Text>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.replace('/(auth)/login')}
          >
            <Text style={styles.primaryButtonText}>Sign In</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { paddingTop: insets.top }]}>
        <ActivityIndicator size="large" color="#1A1A1A" />
        <Text style={styles.loadingText}>Loading invite...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.content}>
          <Ionicons name="alert-circle-outline" size={64} color="#E74C3C" />
          <Text style={styles.title}>Invalid Invite</Text>
          <Text style={styles.subtitle}>{error}</Text>
          <TouchableOpacity style={styles.primaryButton} onPress={goBack}>
            <Text style={styles.primaryButtonText}>Go Home</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (!inviteInfo) {
    return null;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <TouchableOpacity style={styles.closeButton} onPress={goBack}>
        <Ionicons name="close" size={24} color="#1A1A1A" />
      </TouchableOpacity>

      <View style={styles.content}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {inviteInfo.display_name[0].toUpperCase()}
          </Text>
        </View>

        <Text style={styles.inviteLabel}>You've been invited by</Text>
        <Text style={styles.displayName}>{inviteInfo.display_name}</Text>

        <View style={styles.statsContainer}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{inviteInfo.posts_count}</Text>
            <Text style={styles.statLabel}>Posts</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.stat}>
            <Text style={styles.statValue}>{inviteInfo.friends_count}</Text>
            <Text style={styles.statLabel}>Friends</Text>
          </View>
        </View>

        {inviteInfo.is_self ? (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={20} color="#666" />
            <Text style={styles.infoText}>This is your own invite link</Text>
          </View>
        ) : inviteInfo.is_already_friend ? (
          <View style={styles.successBox}>
            <Ionicons name="checkmark-circle" size={20} color="#27AE60" />
            <Text style={styles.successText}>Already friends!</Text>
          </View>
        ) : inviteInfo.request_pending ? (
          <View style={styles.pendingBox}>
            <Ionicons name="time" size={20} color="#F57C00" />
            <Text style={styles.pendingText}>Friend request pending</Text>
          </View>
        ) : (
          <>
            <TouchableOpacity
              style={[styles.acceptButton, accepting && styles.acceptButtonDisabled]}
              onPress={acceptInvite}
              disabled={accepting}
            >
              {accepting ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <>
                  <Ionicons name="people" size={20} color="#FFF" />
                  <Text style={styles.acceptButtonText}>Accept & Become Friends</Text>
                </>
              )}
            </TouchableOpacity>
            <Text style={styles.note}>
              You'll be connected instantly when you accept
            </Text>
          </>
        )}

        <TouchableOpacity style={styles.secondaryButton} onPress={goBack}>
          <Text style={styles.secondaryButtonText}>
            {inviteInfo.is_already_friend || inviteInfo.is_self ? 'Go to Feed' : 'Maybe Later'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF8',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    zIndex: 10,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#F5F5F3',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  avatarText: {
    fontSize: 40,
    fontWeight: '600',
    color: '#FFF',
  },
  inviteLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
  },
  displayName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 24,
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  stat: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  statLabel: {
    fontSize: 13,
    color: '#888',
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    backgroundColor: '#E5E5E0',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A1A',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 32,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F3',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
  },
  successBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 10,
  },
  successText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#27AE60',
  },
  pendingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 10,
  },
  pendingText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F57C00',
  },
  acceptButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 32,
    gap: 10,
    width: '100%',
    marginBottom: 12,
  },
  acceptButtonDisabled: {
    backgroundColor: '#CCC',
  },
  acceptButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
  note: {
    fontSize: 13,
    color: '#999',
    marginBottom: 24,
  },
  primaryButton: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 32,
    width: '100%',
    alignItems: 'center',
    marginBottom: 16,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF',
  },
  secondaryButton: {
    padding: 16,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#888',
  },
});
