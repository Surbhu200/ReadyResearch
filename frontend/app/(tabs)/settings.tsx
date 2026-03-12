import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  Share,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { useAuth } from '../../context/AuthContext';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface InviteLink {
  invite_code: string;
  invite_url: string;
  user_id: string;
  display_name: string;
}

export default function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const { user, token, logout, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [saving, setSaving] = useState(false);
  
  // Invite link state
  const [inviteLink, setInviteLink] = useState<InviteLink | null>(null);
  const [loadingInvite, setLoadingInvite] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    fetchInviteLink();
  }, [token]);

  const fetchInviteLink = async () => {
    if (!token) return;
    setLoadingInvite(true);
    try {
      const response = await fetch(`${API_URL}/api/invite/my-link`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setInviteLink(data);
      }
    } catch (error) {
      console.error('Error fetching invite link:', error);
    } finally {
      setLoadingInvite(false);
    }
  };

  const regenerateInviteLink = async () => {
    if (!token) return;
    setRegenerating(true);
    try {
      const response = await fetch(`${API_URL}/api/invite/regenerate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setInviteLink(data);
        Alert.alert('Success', 'Your invite link has been regenerated');
      }
    } catch (error) {
      console.error('Error regenerating invite link:', error);
      Alert.alert('Error', 'Failed to regenerate invite link');
    } finally {
      setRegenerating(false);
    }
  };

  const shareInviteLink = async () => {
    if (!inviteLink) return;
    
    try {
      const message = `Join me on TextBlurb! Click this link to add me as a friend: ${inviteLink.invite_url}`;
      
      if (Platform.OS === 'web') {
        // On web, copy to clipboard
        await Clipboard.setStringAsync(inviteLink.invite_url);
        Alert.alert('Copied!', 'Invite link copied to clipboard');
      } else {
        // On mobile, use native share
        await Share.share({
          message,
          url: inviteLink.invite_url,
        });
      }
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const copyInviteCode = async () => {
    if (!inviteLink) return;
    try {
      await Clipboard.setStringAsync(inviteLink.invite_code);
      Alert.alert('Copied!', 'Invite code copied to clipboard');
    } catch (error) {
      console.error('Error copying:', error);
    }
  };

  const handleSaveProfile = async () => {
    if (!displayName.trim()) {
      Alert.alert('Error', 'Display name cannot be empty');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          display_name: displayName.trim(),
          phone: phone.trim() || null,
        }),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        updateUser(updatedUser);
        setIsEditing(false);
        Alert.alert('Success', 'Profile updated successfully');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to update profile');
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      // Laptop/Browser version
      const confirmed = window.confirm('Are you sure you want to sign out?');
      if (confirmed) {
        logout();
      }
    } else {
      // Phone/Mobile version
      Alert.alert(
        'Sign out',
        'Are you sure you want to sign out?',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Sign out', style: 'destructive', onPress: logout },
        ]
      );
    }
  };

  const cancelEdit = () => {
    setDisplayName(user?.display_name || '');
    setPhone(user?.phone || '');
    setIsEditing(false);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Profile Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Profile</Text>
            {!isEditing ? (
              <TouchableOpacity onPress={() => setIsEditing(true)}>
                <Text style={styles.editButton}>Edit</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity onPress={cancelEdit}>
                <Text style={styles.cancelButton}>Cancel</Text>
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.profileCard}>
            <View style={styles.avatarLarge}>
              <Text style={styles.avatarLargeText}>
                {user?.display_name?.[0]?.toUpperCase() || '?'}
              </Text>
            </View>

            {isEditing ? (
              <View style={styles.editForm}>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Display Name</Text>
                  <TextInput
                    style={styles.input}
                    value={displayName}
                    onChangeText={setDisplayName}
                    placeholder="Your name"
                  />
                </View>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Phone Number</Text>
                  <TextInput
                    style={styles.input}
                    value={phone}
                    onChangeText={setPhone}
                    placeholder="+1 234 567 8900"
                    keyboardType="phone-pad"
                  />
                </View>
                <TouchableOpacity
                  style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                  onPress={handleSaveProfile}
                  disabled={saving}
                >
                  {saving ? (
                    <ActivityIndicator color="#FFF" size="small" />
                  ) : (
                    <Text style={styles.saveButtonText}>Save Changes</Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.profileInfo}>
                <Text style={styles.profileName}>{user?.display_name}</Text>
                <Text style={styles.profileEmail}>{user?.email}</Text>
                {user?.phone && (
                  <Text style={styles.profilePhone}>{user.phone}</Text>
                )}
                <View style={styles.statsRow}>
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{user?.posts_count || 0}</Text>
                    <Text style={styles.statLabel}>Posts</Text>
                  </View>
                  <View style={styles.statDivider} />
                  <View style={styles.statItem}>
                    <Text style={styles.statValue}>{user?.friends_count || 0}</Text>
                    <Text style={styles.statLabel}>Friends</Text>
                  </View>
                </View>
              </View>
            )}
          </View>
        </View>

        {/* Invite Link Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Invite Friends</Text>
          
          <View style={styles.inviteCard}>
            <View style={styles.inviteHeader}>
              <Ionicons name="link" size={24} color="#1A1A1A" />
              <Text style={styles.inviteTitle}>Your Invite Link</Text>
            </View>
            
            <Text style={styles.inviteDescription}>
              Share this link with friends. When they click it, you'll be connected instantly!
            </Text>

            {loadingInvite ? (
              <ActivityIndicator size="small" color="#1A1A1A" style={{ marginVertical: 16 }} />
            ) : inviteLink ? (
              <>
                <View style={styles.inviteCodeContainer}>
                  <View style={styles.inviteCodeBox}>
                    <Text style={styles.inviteCodeLabel}>Code</Text>
                    <Text style={styles.inviteCode}>{inviteLink.invite_code}</Text>
                  </View>
                  <TouchableOpacity style={styles.copyButton} onPress={copyInviteCode}>
                    <Ionicons name="copy-outline" size={20} color="#1A1A1A" />
                  </TouchableOpacity>
                </View>

                <TouchableOpacity
                  style={styles.shareButton}
                  onPress={shareInviteLink}
                  activeOpacity={0.8}
                >
                  <Ionicons name="share-outline" size={20} color="#FFF" />
                  <Text style={styles.shareButtonText}>
                    {Platform.OS === 'web' ? 'Copy Invite Link' : 'Share Invite Link'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.regenerateButton}
                  onPress={regenerateInviteLink}
                  disabled={regenerating}
                >
                  {regenerating ? (
                    <ActivityIndicator size="small" color="#666" />
                  ) : (
                    <>
                      <Ionicons name="refresh-outline" size={16} color="#666" />
                      <Text style={styles.regenerateButtonText}>Generate New Code</Text>
                    </>
                  )}
                </TouchableOpacity>
              </>
            ) : null}
          </View>
        </View>

        {/* Account Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>

          <TouchableOpacity style={styles.menuItem} onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={22} color="#E74C3C" />
            <Text style={[styles.menuItemText, styles.logoutText]}>Sign Out</Text>
            <Ionicons name="chevron-forward" size={20} color="#CCC" />
          </TouchableOpacity>
        </View>

        {/* App Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <View style={styles.infoCard}>
            <Text style={styles.appName}>TextBlurb</Text>
            <Text style={styles.appVersion}>Version 1.1.0</Text>
            <Text style={styles.appDescription}>
              Share interesting reads with friends. A minimalist text-sharing platform.
            </Text>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF8',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  editButton: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  cancelButton: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E74C3C',
  },
  profileCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarLargeText: {
    fontSize: 32,
    fontWeight: '600',
    color: '#FFF',
  },
  profileInfo: {
    alignItems: 'center',
  },
  profileName: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  profileEmail: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  profilePhone: {
    fontSize: 14,
    color: '#888',
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#F0F0ED',
  },
  statItem: {
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
    backgroundColor: '#F0F0ED',
  },
  editForm: {
    width: '100%',
    marginTop: 8,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#F5F5F3',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    color: '#1A1A1A',
  },
  saveButton: {
    backgroundColor: '#1A1A1A',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonDisabled: {
    backgroundColor: '#CCC',
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  // Invite Link styles
  inviteCard: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  inviteHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  inviteTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  inviteDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 16,
  },
  inviteCodeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  inviteCodeBox: {
    flex: 1,
    backgroundColor: '#F5F5F3',
    borderRadius: 10,
    padding: 14,
  },
  inviteCodeLabel: {
    fontSize: 11,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  inviteCode: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: 2,
  },
  copyButton: {
    width: 48,
    height: 48,
    borderRadius: 10,
    backgroundColor: '#F5F5F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 14,
    gap: 10,
  },
  shareButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  regenerateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    padding: 10,
    gap: 6,
  },
  regenerateButtonText: {
    fontSize: 14,
    color: '#666',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  menuItemText: {
    flex: 1,
    fontSize: 16,
    color: '#1A1A1A',
    marginLeft: 14,
  },
  logoutText: {
    color: '#E74C3C',
  },
  infoCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  appName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  appVersion: {
    fontSize: 13,
    color: '#888',
    marginTop: 4,
  },
  appDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 12,
    lineHeight: 20,
  },
});
