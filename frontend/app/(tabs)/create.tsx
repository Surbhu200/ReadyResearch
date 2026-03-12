import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function CreateScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { token } = useAuth();
  const [content, setContent] = useState('');
  const [sourceLink, setSourceLink] = useState('');
  const [sourceTitle, setSourceTitle] = useState('');
  const [loading, setLoading] = useState(false);

  const validateUrl = (url: string): boolean => {
    if (!url) return true;
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      Alert.alert('Missing content', 'Please enter the text you want to share.');
      return;
    }

    if (content.length > 2000) {
      Alert.alert('Too long', 'Please keep your blurb under 2000 characters.');
      return;
    }

    if (sourceLink && !validateUrl(sourceLink)) {
      Alert.alert('Invalid URL', 'Please enter a valid URL or leave it empty.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: content.trim(),
          source_link: sourceLink.trim() || null,
          source_title: sourceTitle.trim() || null,
        }),
      });

      if (response.ok) {
        Alert.alert('Shared!', 'Your blurb has been shared with friends.', [
          {
            text: 'OK',
            onPress: () => {
              setContent('');
              setSourceLink('');
              setSourceTitle('');
              router.push('/(tabs)');
            },
          },
        ]);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to share your blurb.');
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const characterCount = content.length;
  const isOverLimit = characterCount > 2000;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.headerTitle}>Share a Blurb</Text>
        <Text style={styles.headerSubtitle}>
          Share an interesting piece of text with friends
        </Text>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.inputGroup}>
          <Text style={styles.label}>The text you find interesting *</Text>
          <TextInput
            style={[
              styles.contentInput,
              isOverLimit && styles.inputError,
            ]}
            placeholder="Paste or type the text you want to share..."
            placeholderTextColor="#AAA"
            multiline
            value={content}
            onChangeText={setContent}
            textAlignVertical="top"
          />
          <Text
            style={[
              styles.charCount,
              isOverLimit && styles.charCountError,
            ]}
          >
            {characterCount}/2000
          </Text>
        </View>

        <View style={styles.inputGroup}>
          <View style={styles.labelRow}>
            <Ionicons name="link-outline" size={16} color="#666" />
            <Text style={styles.labelText}>Source link (optional)</Text>
          </View>
          <TextInput
            style={styles.input}
            placeholder="https://example.com/article"
            placeholderTextColor="#AAA"
            value={sourceLink}
            onChangeText={setSourceLink}
            autoCapitalize="none"
            keyboardType="url"
          />
        </View>

        <View style={styles.inputGroup}>
          <View style={styles.labelRow}>
            <Ionicons name="document-text-outline" size={16} color="#666" />
            <Text style={styles.labelText}>Source title (optional)</Text>
          </View>
          <TextInput
            style={styles.input}
            placeholder="e.g., The New York Times, Medium"
            placeholderTextColor="#AAA"
            value={sourceTitle}
            onChangeText={setSourceTitle}
          />
        </View>

        <TouchableOpacity
          style={[
            styles.submitButton,
            (!content.trim() || isOverLimit || loading) && styles.submitButtonDisabled,
          ]}
          onPress={handleSubmit}
          disabled={!content.trim() || isOverLimit || loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Ionicons name="paper-plane-outline" size={20} color="#FFF" />
              <Text style={styles.submitButtonText}>Share Blurb</Text>
            </>
          )}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF8',
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 24,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#444',
    marginBottom: 8,
  },
  labelText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#444',
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5E0',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    color: '#1A1A1A',
  },
  contentInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E5E0',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    color: '#1A1A1A',
    minHeight: 180,
    lineHeight: 24,
  },
  inputError: {
    borderColor: '#E74C3C',
  },
  charCount: {
    fontSize: 12,
    color: '#999',
    textAlign: 'right',
    marginTop: 8,
  },
  charCountError: {
    color: '#E74C3C',
  },
  submitButton: {
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 8,
  },
  submitButtonDisabled: {
    backgroundColor: '#CCC',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
