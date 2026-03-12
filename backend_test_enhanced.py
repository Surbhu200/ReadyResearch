#!/usr/bin/env python3
"""
Enhanced backend API tests for TextBlurb social app.
Tests new endpoints: discover, profile, view tracking, and comments.
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Get backend URL from environment - using the external URL from frontend/.env
BACKEND_URL = "https://word-swap-2.preview.emergentagent.com/api"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
        
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.errors:
            print(f"\n=== FAILURES ===")
            for error in self.errors:
                print(f"- {error}")
                
        return self.failed == 0

def create_test_user(result: TestResult, suffix: str = "") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Create a test user and return (user_id, token, display_name)"""
    import random
    random_num = random.randint(100000, 999999)
    user_data = {
        "email": f"testuser{suffix}{random_num}@textblurb.com",
        "password": "secure123456",
        "display_name": f"Test User{suffix}",
        "phone": f"+123456{random_num}{suffix}"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data["user"]["id"]
            token = data["access_token"]
            display_name = data["user"]["display_name"]
            result.add_pass(f"User Registration{suffix}")
            return user_id, token, display_name
        else:
            result.add_fail(f"User Registration{suffix}", f"Status {response.status_code}: {response.text}")
            return None, None, None
    except Exception as e:
        result.add_fail(f"User Registration{suffix}", f"Request failed: {str(e)}")
        return None, None, None

def login_user(result: TestResult, email: str, password: str, suffix: str = "") -> Tuple[Optional[str], Optional[str]]:
    """Login user and return (user_id, token)"""
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            user_id = data["user"]["id"]
            token = data["access_token"]
            result.add_pass(f"User Login{suffix}")
            return user_id, token
        else:
            result.add_fail(f"User Login{suffix}", f"Status {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        result.add_fail(f"User Login{suffix}", f"Request failed: {str(e)}")
        return None, None

def create_test_post(result: TestResult, token: str, content: str, suffix: str = "") -> Optional[str]:
    """Create a test post and return post_id"""
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {
        "content": content,
        "source_link": "https://example.com/inspiration",
        "source_title": "Daily Inspiration"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/posts", json=post_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            post_id = data["id"]
            result.add_pass(f"Create Post{suffix}")
            return post_id
        else:
            result.add_fail(f"Create Post{suffix}", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.add_fail(f"Create Post{suffix}", f"Request failed: {str(e)}")
        return None

def test_discover_feed(result: TestResult, token: str):
    """Test GET /api/posts/discover - Get popular posts for discovery feed"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/posts/discover", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.add_pass("GET /api/posts/discover - Returns list of posts")
                
                # Check if posts have required fields
                if data:
                    post = data[0]
                    required_fields = ["id", "content", "author_id", "author_name", "created_at", "likes", "views"]
                    if all(field in post for field in required_fields):
                        result.add_pass("GET /api/posts/discover - Posts have required fields")
                    else:
                        missing = [f for f in required_fields if f not in post]
                        result.add_fail("GET /api/posts/discover - Fields", f"Missing fields: {missing}")
                else:
                    result.add_pass("GET /api/posts/discover - Empty list (no posts yet)")
                    
            else:
                result.add_fail("GET /api/posts/discover", f"Expected list, got {type(data)}")
        else:
            result.add_fail("GET /api/posts/discover", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/posts/discover", f"Request failed: {str(e)}")

def test_discover_feed_pagination(result: TestResult, token: str):
    """Test pagination on discover feed"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/posts/discover?skip=0&limit=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) <= 5:
                result.add_pass("GET /api/posts/discover - Pagination works")
            else:
                result.add_fail("GET /api/posts/discover - Pagination", f"Expected max 5 posts, got {len(data)}")
        else:
            result.add_fail("GET /api/posts/discover - Pagination", f"Status {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts/discover - Pagination", f"Request failed: {str(e)}")

def test_user_profile(result: TestResult, token: str, user_id: str, other_user_id: str):
    """Test GET /api/users/{user_id}/profile - Get user profile with stats"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test getting own profile
    try:
        response = requests.get(f"{BACKEND_URL}/users/{user_id}/profile", headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "display_name", "friends_count", "posts_count", "total_likes", "is_friend", "is_self"]
            if all(field in data for field in required_fields):
                result.add_pass("GET /api/users/{id}/profile - Returns profile with all fields")
                
                # Verify is_self is True for own profile
                if data["is_self"]:
                    result.add_pass("GET /api/users/{id}/profile - is_self=True for own profile")
                else:
                    result.add_fail("GET /api/users/{id}/profile - is_self", f"Expected True, got {data['is_self']}")
                    
            else:
                missing = [f for f in required_fields if f not in data]
                result.add_fail("GET /api/users/{id}/profile", f"Missing fields: {missing}")
        else:
            result.add_fail("GET /api/users/{id}/profile", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/users/{id}/profile", f"Request failed: {str(e)}")
    
    # Test getting other user's profile
    try:
        response = requests.get(f"{BACKEND_URL}/users/{other_user_id}/profile", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data["id"] == other_user_id:
                result.add_pass("GET /api/users/{id}/profile - Returns other user profile")
                
                # Verify is_self is False for other user
                if not data["is_self"]:
                    result.add_pass("GET /api/users/{id}/profile - is_self=False for other user")
                else:
                    result.add_fail("GET /api/users/{id}/profile - is_self other", f"Expected False, got {data['is_self']}")
            else:
                result.add_fail("GET /api/users/{id}/profile - Other", f"Wrong user ID returned")
        else:
            result.add_fail("GET /api/users/{id}/profile - Other", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/users/{id}/profile - Other", f"Request failed: {str(e)}")

def test_user_profile_404(result: TestResult, token: str):
    """Test user profile with non-existent user"""
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    
    try:
        response = requests.get(f"{BACKEND_URL}/users/{fake_id}/profile", headers=headers)
        if response.status_code == 404:
            result.add_pass("GET /api/users/{id}/profile - 404 for non-existent user")
        else:
            result.add_fail("GET /api/users/{id}/profile - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/users/{id}/profile - 404", f"Request failed: {str(e)}")

def test_post_view_tracking(result: TestResult, token: str, post_id: str):
    """Test POST /api/posts/{post_id}/view - Record a view for retention tracking"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get initial view count
    try:
        get_response = requests.get(f"{BACKEND_URL}/posts/{post_id}", headers=headers)
        if get_response.status_code == 200:
            initial_views = get_response.json().get("views", 0)
            
            # Record a view
            view_response = requests.post(f"{BACKEND_URL}/posts/{post_id}/view", headers=headers)
            if view_response.status_code == 200:
                result.add_pass("POST /api/posts/{id}/view - Records view")
                
                # Verify view count increased (get post again)
                get_response2 = requests.get(f"{BACKEND_URL}/posts/{post_id}", headers=headers)
                if get_response2.status_code == 200:
                    new_views = get_response2.json().get("views", 0)
                    if new_views == initial_views + 1:
                        result.add_pass("POST /api/posts/{id}/view - Increments view count")
                        
                        # Test viewing same post again (should not increment for same user)
                        view_response2 = requests.post(f"{BACKEND_URL}/posts/{post_id}/view", headers=headers)
                        if view_response2.status_code == 200:
                            get_response3 = requests.get(f"{BACKEND_URL}/posts/{post_id}", headers=headers)
                            if get_response3.status_code == 200:
                                final_views = get_response3.json().get("views", 0)
                                if final_views == new_views:  # Should not increment again
                                    result.add_pass("POST /api/posts/{id}/view - Only once per user")
                                else:
                                    result.add_fail("POST /api/posts/{id}/view - Once per user", f"Views incremented again: {final_views}")
                    else:
                        result.add_fail("POST /api/posts/{id}/view - View count", f"Expected {initial_views + 1}, got {new_views}")
            else:
                result.add_fail("POST /api/posts/{id}/view", f"Status {view_response.status_code}: {view_response.text}")
        else:
            result.add_fail("POST /api/posts/{id}/view - Get initial", f"Status {get_response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/view", f"Request failed: {str(e)}")

def test_view_tracking_404(result: TestResult, token: str):
    """Test view tracking on non-existent post"""
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{fake_id}/view", headers=headers)
        if response.status_code == 404:
            result.add_pass("POST /api/posts/{id}/view - 404 for non-existent post")
        else:
            result.add_fail("POST /api/posts/{id}/view - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/view - 404", f"Request failed: {str(e)}")

def test_comments_creation(result: TestResult, token: str, post_id: str) -> Optional[str]:
    """Test POST /api/posts/{post_id}/comments - Create a comment"""
    headers = {"Authorization": f"Bearer {token}"}
    comment_data = {
        "content": "This is a great post! Thanks for sharing this inspiring content."
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/comments", json=comment_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "post_id", "author_id", "author_name", "content", "created_at"]
            if all(field in data for field in required_fields):
                result.add_pass("POST /api/posts/{id}/comments - Creates comment with all fields")
                
                # Verify content matches
                if data["content"] == comment_data["content"]:
                    result.add_pass("POST /api/posts/{id}/comments - Content matches")
                else:
                    result.add_fail("POST /api/posts/{id}/comments - Content", f"Content mismatch")
                
                # Verify post_id matches
                if data["post_id"] == post_id:
                    result.add_pass("POST /api/posts/{id}/comments - Post ID matches")
                    return data["id"]
                else:
                    result.add_fail("POST /api/posts/{id}/comments - Post ID", f"Post ID mismatch")
                    return None
            else:
                missing = [f for f in required_fields if f not in data]
                result.add_fail("POST /api/posts/{id}/comments", f"Missing fields: {missing}")
                return None
        else:
            result.add_fail("POST /api/posts/{id}/comments", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/comments", f"Request failed: {str(e)}")
        return None

def test_comments_validation(result: TestResult, token: str, post_id: str):
    """Test comment validation errors"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test empty content
    try:
        empty_comment = {"content": ""}
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/comments", json=empty_comment, headers=headers)
        if response.status_code == 422:
            result.add_pass("POST /api/posts/{id}/comments - Empty content validation")
        else:
            result.add_fail("POST /api/posts/{id}/comments - Validation", f"Expected 422, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/comments - Validation", f"Request failed: {str(e)}")
    
    # Test content too long (over 500 chars)
    try:
        long_comment = {"content": "A" * 501}
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/comments", json=long_comment, headers=headers)
        if response.status_code == 422:
            result.add_pass("POST /api/posts/{id}/comments - Content too long validation")
        else:
            result.add_fail("POST /api/posts/{id}/comments - Long validation", f"Expected 422, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/comments - Long validation", f"Request failed: {str(e)}")

def test_comments_on_nonexistent_post(result: TestResult, token: str):
    """Test creating comment on non-existent post"""
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    comment_data = {"content": "This won't work"}
    
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{fake_id}/comments", json=comment_data, headers=headers)
        if response.status_code == 404:
            result.add_pass("POST /api/posts/{id}/comments - 404 for non-existent post")
        else:
            result.add_fail("POST /api/posts/{id}/comments - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/comments - 404", f"Request failed: {str(e)}")

def test_get_comments(result: TestResult, token: str, post_id: str):
    """Test GET /api/posts/{post_id}/comments - Get comments for a post"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/posts/{post_id}/comments", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                result.add_pass("GET /api/posts/{id}/comments - Returns list of comments")
                
                if data:  # If there are comments
                    comment = data[0]
                    required_fields = ["id", "post_id", "author_id", "author_name", "content", "created_at"]
                    if all(field in comment for field in required_fields):
                        result.add_pass("GET /api/posts/{id}/comments - Comments have required fields")
                        
                        # Check if sorted by created_at (oldest first)
                        if len(data) > 1:
                            timestamps = [datetime.fromisoformat(c["created_at"].replace('Z', '+00:00')) for c in data]
                            if timestamps == sorted(timestamps):
                                result.add_pass("GET /api/posts/{id}/comments - Sorted by created_at")
                            else:
                                result.add_fail("GET /api/posts/{id}/comments - Sorting", "Comments not sorted by created_at")
                    else:
                        missing = [f for f in required_fields if f not in comment]
                        result.add_fail("GET /api/posts/{id}/comments - Fields", f"Missing fields: {missing}")
                else:
                    result.add_pass("GET /api/posts/{id}/comments - Empty list (no comments yet)")
            else:
                result.add_fail("GET /api/posts/{id}/comments", f"Expected list, got {type(data)}")
        else:
            result.add_fail("GET /api/posts/{id}/comments", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("GET /api/posts/{id}/comments", f"Request failed: {str(e)}")

def test_get_comments_pagination(result: TestResult, token: str, post_id: str):
    """Test pagination on comments"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/posts/{post_id}/comments?skip=0&limit=3", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) <= 3:
                result.add_pass("GET /api/posts/{id}/comments - Pagination works")
            else:
                result.add_fail("GET /api/posts/{id}/comments - Pagination", f"Expected max 3 comments, got {len(data)}")
        else:
            result.add_fail("GET /api/posts/{id}/comments - Pagination", f"Status {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts/{id}/comments - Pagination", f"Request failed: {str(e)}")

def test_get_comments_nonexistent_post(result: TestResult, token: str):
    """Test getting comments for non-existent post"""
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    
    try:
        response = requests.get(f"{BACKEND_URL}/posts/{fake_id}/comments", headers=headers)
        if response.status_code == 404:
            result.add_pass("GET /api/posts/{id}/comments - 404 for non-existent post")
        else:
            result.add_fail("GET /api/posts/{id}/comments - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts/{id}/comments - 404", f"Request failed: {str(e)}")

def test_delete_comment(result: TestResult, token: str, comment_id: str):
    """Test DELETE /api/comments/{comment_id} - Delete a comment"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(f"{BACKEND_URL}/comments/{comment_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "deleted" in data["message"].lower():
                result.add_pass("DELETE /api/comments/{id} - Successful deletion")
            else:
                result.add_fail("DELETE /api/comments/{id}", f"Unexpected response: {data}")
        else:
            result.add_fail("DELETE /api/comments/{id}", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("DELETE /api/comments/{id}", f"Request failed: {str(e)}")

def test_delete_comment_unauthorized(result: TestResult, other_token: str, comment_id: str):
    """Test deleting someone else's comment (should fail)"""
    headers = {"Authorization": f"Bearer {other_token}"}
    
    try:
        response = requests.delete(f"{BACKEND_URL}/comments/{comment_id}", headers=headers)
        if response.status_code == 403:
            result.add_pass("DELETE /api/comments/{id} - 403 for unauthorized deletion")
        else:
            result.add_fail("DELETE /api/comments/{id} - Auth", f"Expected 403, got {response.status_code}")
    except Exception as e:
        result.add_fail("DELETE /api/comments/{id} - Auth", f"Request failed: {str(e)}")

def test_delete_nonexistent_comment(result: TestResult, token: str):
    """Test deleting non-existent comment"""
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())
    
    try:
        response = requests.delete(f"{BACKEND_URL}/comments/{fake_id}", headers=headers)
        if response.status_code == 404:
            result.add_pass("DELETE /api/comments/{id} - 404 for non-existent comment")
        else:
            result.add_fail("DELETE /api/comments/{id} - 404", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("DELETE /api/comments/{id} - 404", f"Request failed: {str(e)}")

def test_authentication_required(result: TestResult):
    """Test that all new endpoints require authentication"""
    endpoints = [
        ("GET", "/posts/discover"),
        ("GET", "/users/some-user-id/profile"),
        ("POST", "/posts/some-post-id/view"),
        ("POST", "/posts/some-post-id/comments"),
        ("GET", "/posts/some-post-id/comments"),
        ("DELETE", "/comments/some-comment-id")
    ]
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BACKEND_URL}{endpoint}", json={})
            elif method == "DELETE":
                response = requests.delete(f"{BACKEND_URL}{endpoint}")
            
            if response.status_code == 401 or response.status_code == 403:
                result.add_pass(f"{method} {endpoint} - Requires authentication")
            else:
                result.add_fail(f"{method} {endpoint} - Auth", f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            result.add_fail(f"{method} {endpoint} - Auth", f"Request failed: {str(e)}")

def main():
    """Run all enhanced backend API tests following the test flow"""
    print("🚀 Starting Enhanced TextBlurb Backend API Tests")
    print(f"Testing endpoint: {BACKEND_URL}")
    print("Testing new endpoints: discover, profile, view tracking, and comments")
    print("=" * 80)
    
    result = TestResult()
    
    # Test authentication requirements first
    print("\n📋 Testing authentication requirements...")
    test_authentication_required(result)
    
    # Step 1: Create test users and login
    print("\n👥 Setting up test users...")
    user1_id, user1_token, user1_name = create_test_user(result, "1")
    user2_id, user2_token, user2_name = create_test_user(result, "2")
    
    if not user1_token or not user2_token:
        print("❌ Failed to create test users. Cannot continue with authenticated tests.")
        result.summary()
        return False
    
    # Step 2: Create test posts
    print("\n📝 Creating test posts...")
    post1_id = create_test_post(result, user1_token, "Just discovered an amazing quote about perseverance and never giving up on your dreams!", "1")
    post2_id = create_test_post(result, user2_token, "The beauty of life lies in the small moments that take your breath away.", "2")
    post3_id = create_test_post(result, user1_token, "Innovation distinguishes between a leader and a follower - Steve Jobs", "3")
    
    if not post1_id:
        print("❌ Failed to create test posts. Cannot continue with post-dependent tests.")
        result.summary()
        return False
    
    # Step 3: Test discover feed
    print("\n🔍 Testing discover feed...")
    test_discover_feed(result, user1_token)
    test_discover_feed_pagination(result, user1_token)
    
    # Step 4: Test view tracking
    print("\n👁️ Testing view tracking...")
    test_post_view_tracking(result, user2_token, post1_id)  # User2 views User1's post
    test_view_tracking_404(result, user1_token)
    
    # Step 5: Test user profiles
    print("\n👤 Testing user profiles...")
    test_user_profile(result, user1_token, user1_id, user2_id)
    test_user_profile_404(result, user1_token)
    
    # Step 6: Test comments
    print("\n💬 Testing comments...")
    comment1_id = test_comments_creation(result, user2_token, post1_id)  # User2 comments on User1's post
    comment2_id = test_comments_creation(result, user1_token, post1_id)  # User1 comments on own post
    
    test_comments_validation(result, user1_token, post1_id)
    test_comments_on_nonexistent_post(result, user1_token)
    
    # Step 7: Test getting comments
    print("\n📖 Testing comment retrieval...")
    test_get_comments(result, user1_token, post1_id)
    test_get_comments_pagination(result, user1_token, post1_id)
    test_get_comments_nonexistent_post(result, user1_token)
    
    # Step 8: Test comment deletion
    print("\n🗑️ Testing comment deletion...")
    if comment1_id and comment2_id:
        # Test unauthorized deletion (User1 tries to delete User2's comment)
        test_delete_comment_unauthorized(result, user1_token, comment1_id)
        
        # Test successful deletion (User2 deletes own comment)
        test_delete_comment(result, user2_token, comment1_id)
    
    test_delete_nonexistent_comment(result, user1_token)
    
    # Print summary
    success = result.summary()
    
    if success:
        print("\n🎉 All enhanced API tests passed! New endpoints are working correctly.")
        print("\n✨ Test flow completed successfully:")
        print("   ✅ User authentication and registration")
        print("   ✅ Post creation and discovery feed")
        print("   ✅ View tracking (retention metrics)")
        print("   ✅ User profile with statistics")
        print("   ✅ Comment creation and retrieval")
        print("   ✅ Comment deletion with authorization")
    else:
        print(f"\n⚠️  {result.failed} test(s) failed. Please check the issues above.")
    
    return success

if __name__ == "__main__":
    main()