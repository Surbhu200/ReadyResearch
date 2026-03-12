import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Linking,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Post {
  id: string;
  content: string;
  source_link: string | null;
  source_title: string | null;
  author_id: string;
  author_name: string;
  created_at: string;
  likes: number;
  liked_by_user: boolean;
  views: number;
  comments_count: number;
}

interface UserProfile {
  id: string;
  display_name: string;
  created_at: string;
  friends_count: number;
  posts_count: number;
  total_likes: number;
  is_friend: boolean;
  is_self: boolean;
}

interface Comment {
  id: string;
  post_id: string;
  author_id: string;
  author_name: string;
  content: string;
  created_at: string;
}

type FeedTab = 'friends' | 'discover';

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function FeedScreen() {
  const insets = useSafeAreaInsets();
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState<FeedTab>('friends');
  const [friendsPosts, setFriendsPosts] = useState<Post[]>([]);
  const [discoverPosts, setDiscoverPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Profile modal state
  const [profileModalVisible, setProfileModalVisible] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  
  // Comments modal state
  const [commentsModalVisible, setCommentsModalVisible] = useState(false);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  const fetchFriendsPosts = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/api/posts`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setFriendsPosts(data);
      }
    } catch (error) {
      console.error('Error fetching friends posts:', error);
    }
  };

  const fetchDiscoverPosts = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/api/posts/discover`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDiscoverPosts(data);
      }
    } catch (error) {
      console.error('Error fetching discover posts:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchFriendsPosts(), fetchDiscoverPosts()]);
    setLoading(false);
    setRefreshing(false);
  };

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [token])
  );

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const recordView = async (postId: string) => {
    try {
      await fetch(`${API_URL}/api/posts/${postId}/view`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch (error) {
      console.error('Error recording view:', error);
    }
  };

  const handleLike = async (postId: string, isLiked: boolean) => {
    const endpoint = isLiked ? 'unlike' : 'like';
    const posts = activeTab === 'friends' ? friendsPosts : discoverPosts;
    const setPosts = activeTab === 'friends' ? setFriendsPosts : setDiscoverPosts;

    try {
      const response = await fetch(`${API_URL}/api/posts/${postId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const updatedPost = await response.json();
        setPosts((prev) => prev.map((p) => (p.id === postId ? updatedPost : p)));
      }
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const openProfile = async (userId: string) => {
    setProfileLoading(true);
    setProfileModalVisible(true);
    
    try {
      const response = await fetch(`${API_URL}/api/users/${userId}/profile`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const profile = await response.json();
        setSelectedProfile(profile);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setProfileLoading(false);
    }
  };

  const openComments = async (postId: string) => {
    setSelectedPostId(postId);
    setCommentsModalVisible(true);
    setCommentsLoading(true);
    
    // Record view when opening comments
    recordView(postId);
    
    try {
      const response = await fetch(`${API_URL}/api/posts/${postId}/comments`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch (error) {
      console.error('Error fetching comments:', error);
    } finally {
      setCommentsLoading(false);
    }
  };

  const submitComment = async () => {
    if (!newComment.trim() || !selectedPostId) return;
    
    setSubmittingComment(true);
    try {
      const response = await fetch(`${API_URL}/api/posts/${selectedPostId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content: newComment.trim() }),
      });
      
      if (response.ok) {
        const comment = await response.json();
        setComments((prev) => [...prev, comment]);
        setNewComment('');
        
        // Update comments count in posts
        const updatePosts = (posts: Post[]) =>
          posts.map((p) =>
            p.id === selectedPostId
              ? { ...p, comments_count: p.comments_count + 1 }
              : p
          );
        setFriendsPosts(updatePosts);
        setDiscoverPosts(updatePosts);
      }
    } catch (error) {
      console.error('Error posting comment:', error);
    } finally {
      setSubmittingComment(false);
    }
  };

  const sendFriendRequest = async (userId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/friends/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ to_user_id: userId }),
      });
      if (response.ok) {
        Alert.alert('Success', 'Friend request sent!');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to send request');
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong');
    }
  };

  const openSourceLink = (url: string) => {
    Linking.openURL(url);
  };

  const currentPosts = activeTab === 'friends' ? friendsPosts : discoverPosts;

  const renderPost = ({ item }: { item: Post }) => {
    const isOwnPost = item.author_id === user?.id;

    return (
      <View style={styles.postCard}>
        <Text style={styles.postContent}>{item.content}</Text>

        {item.source_link && (
          <TouchableOpacity
            style={styles.sourceContainer}
            onPress={() => openSourceLink(item.source_link!)}
            activeOpacity={0.7}
          >
            <Ionicons name="link-outline" size={14} color="#666" />
            <Text style={styles.sourceText} numberOfLines={1}>
              {item.source_title || 'Read source'}
            </Text>
            <Ionicons name="open-outline" size={12} color="#666" />
          </TouchableOpacity>
        )}

        <View style={styles.postFooter}>
          <TouchableOpacity
            style={styles.authorInfo}
            onPress={() => openProfile(item.author_id)}
            activeOpacity={0.7}
          >
            <View style={styles.authorAvatar}>
              <Text style={styles.authorAvatarText}>
                {item.author_name[0].toUpperCase()}
              </Text>
            </View>
            <View>
              <Text style={[styles.authorName, isOwnPost && styles.ownPostAuthor]}>
                {isOwnPost ? 'You' : item.author_name}
              </Text>
              <Text style={styles.timestamp}>{formatTimeAgo(item.created_at)}</Text>
            </View>
          </TouchableOpacity>

          <View style={styles.postActions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => openComments(item.id)}
              activeOpacity={0.7}
            >
              <Ionicons name="chatbubble-outline" size={18} color="#666" />
              {item.comments_count > 0 && (
                <Text style={styles.actionCount}>{item.comments_count}</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => handleLike(item.id, item.liked_by_user)}
              activeOpacity={0.7}
            >
              <Ionicons
                name={item.liked_by_user ? 'heart' : 'heart-outline'}
                size={18}
                color={item.liked_by_user ? '#E74C3C' : '#666'}
              />
              {item.likes > 0 && (
                <Text style={[styles.actionCount, item.liked_by_user && styles.likedText]}>
                  {item.likes}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  const renderEmptyFriends = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="people-outline" size={64} color="#CCC" />
      <Text style={styles.emptyTitle}>No posts from friends</Text>
      <Text style={styles.emptySubtitle}>
        Add friends to see their posts here, or share something yourself!
      </Text>
    </View>
  );

  const renderEmptyDiscover = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="compass-outline" size={64} color="#CCC" />
      <Text style={styles.emptyTitle}>No posts to discover</Text>
      <Text style={styles.emptySubtitle}>
        Be the first to share something interesting!
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color="#1A1A1A" />
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>TextBlurb</Text>
      </View>

      {/* Feed Tabs */}
      <View style={styles.feedTabs}>
        <TouchableOpacity
          style={[styles.feedTab, activeTab === 'friends' && styles.activeFeedTab]}
          onPress={() => setActiveTab('friends')}
        >
          <Ionicons
            name="people"
            size={18}
            color={activeTab === 'friends' ? '#1A1A1A' : '#999'}
          />
          <Text style={[styles.feedTabText, activeTab === 'friends' && styles.activeFeedTabText]}>
            Friends
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.feedTab, activeTab === 'discover' && styles.activeFeedTab]}
          onPress={() => setActiveTab('discover')}
        >
          <Ionicons
            name="compass"
            size={18}
            color={activeTab === 'discover' ? '#1A1A1A' : '#999'}
          />
          <Text style={[styles.feedTabText, activeTab === 'discover' && styles.activeFeedTabText]}>
            Discover
          </Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={currentPosts}
        renderItem={renderPost}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[
          styles.listContent,
          currentPosts.length === 0 && styles.emptyList,
        ]}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#1A1A1A"
          />
        }
        ListEmptyComponent={activeTab === 'friends' ? renderEmptyFriends : renderEmptyDiscover}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />

      {/* Profile Modal */}
      <Modal
        visible={profileModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setProfileModalVisible(false)}
      >
        <View style={[styles.modalContainer, { paddingTop: insets.top }]}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Profile</Text>
            <TouchableOpacity onPress={() => setProfileModalVisible(false)}>
              <Ionicons name="close" size={24} color="#1A1A1A" />
            </TouchableOpacity>
          </View>

          {profileLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color="#1A1A1A" />
            </View>
          ) : selectedProfile ? (
            <View style={styles.profileContent}>
              <View style={styles.profileAvatar}>
                <Text style={styles.profileAvatarText}>
                  {selectedProfile.display_name[0].toUpperCase()}
                </Text>
              </View>
              <Text style={styles.profileName}>{selectedProfile.display_name}</Text>
              
              <View style={styles.profileStats}>
                <View style={styles.profileStat}>
                  <Text style={styles.profileStatValue}>{selectedProfile.posts_count}</Text>
                  <Text style={styles.profileStatLabel}>Posts</Text>
                </View>
                <View style={styles.profileStatDivider} />
                <View style={styles.profileStat}>
                  <Text style={styles.profileStatValue}>{selectedProfile.total_likes}</Text>
                  <Text style={styles.profileStatLabel}>Likes</Text>
                </View>
                <View style={styles.profileStatDivider} />
                <View style={styles.profileStat}>
                  <Text style={styles.profileStatValue}>{selectedProfile.friends_count}</Text>
                  <Text style={styles.profileStatLabel}>Friends</Text>
                </View>
              </View>

              {!selectedProfile.is_self && !selectedProfile.is_friend && (
                <TouchableOpacity
                  style={styles.addFriendButton}
                  onPress={() => {
                    sendFriendRequest(selectedProfile.id);
                    setProfileModalVisible(false);
                  }}
                >
                  <Ionicons name="person-add" size={18} color="#FFF" />
                  <Text style={styles.addFriendButtonText}>Add Friend</Text>
                </TouchableOpacity>
              )}

              {selectedProfile.is_friend && (
                <View style={styles.friendBadge}>
                  <Ionicons name="checkmark-circle" size={18} color="#27AE60" />
                  <Text style={styles.friendBadgeText}>Friends</Text>
                </View>
              )}
            </View>
          ) : null}
        </View>
      </Modal>

      {/* Comments Modal */}
      <Modal
        visible={commentsModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setCommentsModalVisible(false)}
      >
        <KeyboardAvoidingView
          style={[styles.modalContainer, { paddingTop: insets.top }]}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Comments</Text>
            <TouchableOpacity onPress={() => setCommentsModalVisible(false)}>
              <Ionicons name="close" size={24} color="#1A1A1A" />
            </TouchableOpacity>
          </View>

          {commentsLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color="#1A1A1A" />
            </View>
          ) : (
            <>
              <FlatList
                data={comments}
                keyExtractor={(item) => item.id}
                contentContainerStyle={[
                  styles.commentsList,
                  comments.length === 0 && styles.emptyList,
                ]}
                ListEmptyComponent={
                  <View style={styles.emptyComments}>
                    <Ionicons name="chatbubble-outline" size={48} color="#CCC" />
                    <Text style={styles.emptyCommentsText}>No comments yet</Text>
                    <Text style={styles.emptyCommentsSubtext}>Be the first to comment!</Text>
                  </View>
                }
                renderItem={({ item }) => (
                  <View style={styles.commentItem}>
                    <View style={styles.commentAvatar}>
                      <Text style={styles.commentAvatarText}>
                        {item.author_name[0].toUpperCase()}
                      </Text>
                    </View>
                    <View style={styles.commentContent}>
                      <View style={styles.commentHeader}>
                        <Text style={styles.commentAuthor}>{item.author_name}</Text>
                        <Text style={styles.commentTime}>{formatTimeAgo(item.created_at)}</Text>
                      </View>
                      <Text style={styles.commentText}>{item.content}</Text>
                    </View>
                  </View>
                )}
              />

              <View style={styles.commentInputContainer}>
                <TextInput
                  style={styles.commentInput}
                  placeholder="Write a comment..."
                  placeholderTextColor="#AAA"
                  value={newComment}
                  onChangeText={setNewComment}
                  multiline
                  maxLength={500}
                  onSubmitEditing={submitComment}
                />
                <TouchableOpacity
                  style={[
                    styles.commentSubmitButton,
                    (!newComment.trim() || submittingComment) && styles.commentSubmitButtonDisabled,
                  ]}
                  onPress={submitComment}
                  disabled={!newComment.trim() || submittingComment}
                >
                  {submittingComment ? (
                    <ActivityIndicator size="small" color="#FFF" />
                  ) : (
                    <Ionicons name="send" size={18} color="#FFF" />
                  )}
                </TouchableOpacity>
              </View>
            </>
          )}
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAF8',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.5,
  },
  feedTabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E0',
  },
  feedTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#F5F5F3',
    gap: 8,
  },
  activeFeedTab: {
    backgroundColor: '#1A1A1A',
  },
  feedTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#999',
  },
  activeFeedTabText: {
    color: '#FFF',
  },
  listContent: {
    padding: 16,
  },
  emptyList: {
    flex: 1,
  },
  postCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  postContent: {
    fontSize: 17,
    lineHeight: 26,
    color: '#2C2C2C',
    fontWeight: '400',
    letterSpacing: 0.2,
  },
  sourceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 14,
    backgroundColor: '#F5F5F3',
    borderRadius: 8,
    gap: 8,
  },
  sourceText: {
    flex: 1,
    fontSize: 13,
    color: '#666',
  },
  postFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F0ED',
  },
  authorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  authorAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
  },
  authorAvatarText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  authorName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#444',
  },
  ownPostAuthor: {
    color: '#1A1A1A',
  },
  timestamp: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  postActions: {
    flexDirection: 'row',
    gap: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    gap: 4,
  },
  actionCount: {
    fontSize: 13,
    color: '#666',
  },
  likedText: {
    color: '#E74C3C',
  },
  separator: {
    height: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#FAFAF8',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  // Profile styles
  profileContent: {
    alignItems: 'center',
    padding: 32,
  },
  profileAvatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  profileAvatarText: {
    fontSize: 40,
    fontWeight: '600',
    color: '#FFF',
  },
  profileName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 24,
  },
  profileStats: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  profileStat: {
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  profileStatValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  profileStatLabel: {
    fontSize: 13,
    color: '#888',
    marginTop: 4,
  },
  profileStatDivider: {
    width: 1,
    backgroundColor: '#E5E5E0',
  },
  addFriendButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A1A',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 24,
    gap: 8,
  },
  addFriendButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  friendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 20,
    gap: 8,
  },
  friendBadgeText: {
    color: '#27AE60',
    fontSize: 16,
    fontWeight: '600',
  },
  // Comments styles
  commentsList: {
    padding: 16,
  },
  emptyComments: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyCommentsText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptyCommentsSubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
  commentItem: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 12,
  },
  commentAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
  },
  commentAvatarText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
  commentContent: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 12,
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  commentAuthor: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  commentTime: {
    fontSize: 12,
    color: '#999',
  },
  commentText: {
    fontSize: 14,
    color: '#444',
    lineHeight: 20,
  },
  commentInputContainer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5E0',
    backgroundColor: '#FFF',
    gap: 12,
  },
  commentInput: {
    flex: 1,
    backgroundColor: '#F5F5F3',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
    color: '#1A1A1A',
  },
  commentSubmitButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1A1A1A',
    justifyContent: 'center',
    alignItems: 'center',
  },
  commentSubmitButtonDisabled: {
    backgroundColor: '#CCC',
  },
});
