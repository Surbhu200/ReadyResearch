#!/usr/bin/env python3
"""
Comprehensive backend API tests for TextBlurb authentication and friend system.
Tests all auth endpoints, friend management, and post visibility features.
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Get backend URL from environment - using the external URL from frontend/.env
BACKEND_URL = "https://word-swap-2.preview.emergentagent.com/api"

# Test users data
TEST_USERS = [
    {
        "email": "alice.johnson@example.com",
        "password": "securepass123",
        "display_name": "Alice Johnson",
        "phone": "+1234567890"
    },
    {
        "email": "bob.smith@example.com",
        "password": "bobpassword456",
        "display_name": "Bob Smith",
        "phone": "+1987654321"
    },
    {
        "email": "charlie.brown@example.com",
        "password": "charliepass789",
        "display_name": "Charlie Brown"
        # No phone for this user
    }
]

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

class UserSession:
    def __init__(self, user_data: dict, token: str = None, user_response: dict = None):
        self.user_data = user_data
        self.token = token
        self.user_response = user_response
        
    def get_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

def test_user_registration(result: TestResult) -> List[UserSession]:
    """Test POST /api/auth/register - Register users"""
    user_sessions = []
    
    for i, user_data in enumerate(TEST_USERS):
        try:
            response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "token_type", "user"]
                
                if all(field in data for field in required_fields):
                    user_fields = ["id", "email", "display_name", "created_at"]
                    if all(field in data["user"] for field in user_fields):
                        session = UserSession(user_data, data["access_token"], data["user"])
                        user_sessions.append(session)
                        result.add_pass(f"POST /api/auth/register - User {i+1} registered successfully")
                        
                        # Verify token type
                        if data["token_type"] == "bearer":
                            result.add_pass(f"POST /api/auth/register - User {i+1} token type correct")
                        else:
                            result.add_fail(f"Register User {i+1} token type", f"Expected 'bearer', got '{data['token_type']}'")
                    else:
                        result.add_fail(f"Register User {i+1} user fields", f"Missing user fields in response")
                else:
                    result.add_fail(f"Register User {i+1}", f"Missing required fields: {data}")
            else:
                result.add_fail(f"POST /api/auth/register - User {i+1}", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail(f"POST /api/auth/register - User {i+1}", f"Request failed: {str(e)}")
    
    return user_sessions

def test_duplicate_registration(result: TestResult, existing_user: dict):
    """Test duplicate email registration"""
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=existing_user)
        if response.status_code == 400:
            data = response.json()
            if "already registered" in data.get("detail", "").lower():
                result.add_pass("POST /api/auth/register - Duplicate email rejected")
            else:
                result.add_fail("Duplicate email", f"Wrong error message: {data}")
        else:
            result.add_fail("Duplicate email", f"Expected 400, got {response.status_code}")
    except Exception as e:
        result.add_fail("Duplicate email test", f"Request failed: {str(e)}")

def test_user_login(result: TestResult, user_sessions: List[UserSession]) -> List[UserSession]:
    """Test POST /api/auth/login - Login users"""
    logged_in_sessions = []
    
    for i, session in enumerate(user_sessions):
        login_data = {
            "email": session.user_data["email"],
            "password": session.user_data["password"]
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    # Update session with new token
                    session.token = data["access_token"]
                    session.user_response = data["user"]
                    logged_in_sessions.append(session)
                    result.add_pass(f"POST /api/auth/login - User {i+1} logged in successfully")
                else:
                    result.add_fail(f"Login User {i+1}", f"Missing token or user in response")
            else:
                result.add_fail(f"POST /api/auth/login - User {i+1}", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail(f"POST /api/auth/login - User {i+1}", f"Request failed: {str(e)}")
    
    return logged_in_sessions

def test_invalid_login(result: TestResult):
    """Test login with invalid credentials"""
    invalid_credentials = [
        {"email": "nonexistent@example.com", "password": "wrongpass"},
        {"email": TEST_USERS[0]["email"], "password": "wrongpassword"}
    ]
    
    for i, creds in enumerate(invalid_credentials):
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=creds)
            if response.status_code == 401:
                result.add_pass(f"POST /api/auth/login - Invalid credentials {i+1} rejected")
            else:
                result.add_fail(f"Invalid login {i+1}", f"Expected 401, got {response.status_code}")
        except Exception as e:
            result.add_fail(f"Invalid login {i+1}", f"Request failed: {str(e)}")

def test_get_current_user(result: TestResult, user_sessions: List[UserSession]):
    """Test GET /api/auth/me - Get current user"""
    for i, session in enumerate(user_sessions):
        try:
            response = requests.get(f"{BACKEND_URL}/auth/me", headers=session.get_headers())
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "email", "display_name", "created_at", "friends_count", "posts_count"]
                if all(field in data for field in expected_fields):
                    result.add_pass(f"GET /api/auth/me - User {i+1} data retrieved")
                    # Verify it's the correct user
                    if data["email"] == session.user_data["email"]:
                        result.add_pass(f"GET /api/auth/me - User {i+1} correct identity")
                    else:
                        result.add_fail(f"Current user {i+1}", f"Wrong user returned")
                else:
                    result.add_fail(f"Current user {i+1}", f"Missing fields in response")
            else:
                result.add_fail(f"GET /api/auth/me - User {i+1}", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail(f"GET /api/auth/me - User {i+1}", f"Request failed: {str(e)}")

def test_update_profile(result: TestResult, user_sessions: List[UserSession]):
    """Test PUT /api/auth/profile - Update profile"""
    if not user_sessions:
        return
        
    session = user_sessions[0]
    update_data = {
        "display_name": "Alice Johnson Updated",
        "phone": "+1111111111"
    }
    
    try:
        response = requests.put(f"{BACKEND_URL}/auth/profile", json=update_data, headers=session.get_headers())
        if response.status_code == 200:
            data = response.json()
            if data.get("display_name") == update_data["display_name"]:
                result.add_pass("PUT /api/auth/profile - Display name updated")
            else:
                result.add_fail("Profile update name", f"Name not updated correctly")
                
            if data.get("phone") == update_data["phone"]:
                result.add_pass("PUT /api/auth/profile - Phone updated")
            else:
                result.add_fail("Profile update phone", f"Phone not updated correctly")
        else:
            result.add_fail("PUT /api/auth/profile", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("PUT /api/auth/profile", f"Request failed: {str(e)}")

def test_search_users(result: TestResult, user_sessions: List[UserSession]):
    """Test GET /api/users/search - Search users"""
    if len(user_sessions) < 2:
        return
        
    session = user_sessions[0]
    
    # Search for another user by name
    search_queries = ["Bob", "Charlie", "Smith"]
    
    for query in search_queries:
        try:
            response = requests.get(f"{BACKEND_URL}/users/search?query={query}", headers=session.get_headers())
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    result.add_pass(f"GET /api/users/search - Query '{query}' returned results")
                    # Verify user fields
                    if data:
                        user = data[0]
                        expected_fields = ["id", "email", "display_name"]
                        if all(field in user for field in expected_fields):
                            result.add_pass(f"GET /api/users/search - User fields correct for '{query}'")
                        else:
                            result.add_fail(f"Search user fields {query}", f"Missing fields")
                else:
                    result.add_fail(f"Search {query}", f"Expected list, got {type(data)}")
            else:
                result.add_fail(f"GET /api/users/search - {query}", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail(f"GET /api/users/search - {query}", f"Request failed: {str(e)}")

def test_friend_request_flow(result: TestResult, user_sessions: List[UserSession]) -> Dict[str, str]:
    """Test complete friend request flow"""
    if len(user_sessions) < 2:
        result.add_fail("Friend request flow", "Need at least 2 users")
        return {}
        
    user1, user2 = user_sessions[0], user_sessions[1]
    friend_request_id = None
    
    # Step 1: User1 sends friend request to User2
    try:
        request_data = {"to_user_id": user2.user_response["id"]}
        response = requests.post(f"{BACKEND_URL}/friends/request", json=request_data, headers=user1.get_headers())
        if response.status_code == 200:
            result.add_pass("POST /api/friends/request - Friend request sent")
        else:
            result.add_fail("Friend request send", f"Status code {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        result.add_fail("Friend request send", f"Request failed: {str(e)}")
        return {}
    
    # Step 2: User2 checks incoming requests
    try:
        response = requests.get(f"{BACKEND_URL}/friends/requests/incoming", headers=user2.get_headers())
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                request_item = data[0]
                if "id" in request_item and "from_user" in request_item:
                    friend_request_id = request_item["id"]
                    result.add_pass("GET /api/friends/requests/incoming - Request found")
                    
                    # Verify from_user details
                    if request_item["from_user"]["id"] == user1.user_response["id"]:
                        result.add_pass("GET /api/friends/requests/incoming - Correct sender")
                    else:
                        result.add_fail("Incoming request sender", f"Wrong sender ID")
                else:
                    result.add_fail("Incoming request format", f"Missing fields")
            else:
                result.add_fail("Incoming requests", f"No requests found")
        else:
            result.add_fail("GET /api/friends/requests/incoming", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/friends/requests/incoming", f"Request failed: {str(e)}")
    
    # Step 3: User1 checks outgoing requests
    try:
        response = requests.get(f"{BACKEND_URL}/friends/requests/outgoing", headers=user1.get_headers())
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                result.add_pass("GET /api/friends/requests/outgoing - Request found")
            else:
                result.add_fail("Outgoing requests", f"No requests found")
        else:
            result.add_fail("GET /api/friends/requests/outgoing", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/friends/requests/outgoing", f"Request failed: {str(e)}")
    
    # Step 4: User2 accepts the friend request
    if friend_request_id:
        try:
            response = requests.post(f"{BACKEND_URL}/friends/requests/{friend_request_id}/accept", headers=user2.get_headers())
            if response.status_code == 200:
                result.add_pass("POST /api/friends/requests/{id}/accept - Request accepted")
            else:
                result.add_fail("Accept friend request", f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            result.add_fail("Accept friend request", f"Request failed: {str(e)}")
    
    # Step 5: Verify they are now friends
    for i, session in enumerate([user1, user2]):
        try:
            response = requests.get(f"{BACKEND_URL}/friends", headers=session.get_headers())
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    result.add_pass(f"GET /api/friends - User {i+1} has friends")
                    # Check if the friend is the other user
                    friend_ids = [friend["id"] for friend in data]
                    expected_friend_id = user2.user_response["id"] if i == 0 else user1.user_response["id"]
                    if expected_friend_id in friend_ids:
                        result.add_pass(f"GET /api/friends - User {i+1} friends list correct")
                    else:
                        result.add_fail(f"Friends list {i+1}", f"Expected friend not found")
                else:
                    result.add_fail(f"Friends list {i+1}", f"No friends found")
            else:
                result.add_fail(f"GET /api/friends - User {i+1}", f"Status code {response.status_code}")
        except Exception as e:
            result.add_fail(f"GET /api/friends - User {i+1}", f"Request failed: {str(e)}")
    
    return {"user1": user1.user_response["id"], "user2": user2.user_response["id"]}

def test_posts_with_friends(result: TestResult, user_sessions: List[UserSession], friends_info: Dict[str, str]):
    """Test post creation and visibility with friends"""
    if len(user_sessions) < 2:
        return
        
    user1, user2 = user_sessions[0], user_sessions[1]
    
    # User1 creates a post
    post_data = {
        "content": "This is a private post from Alice that only friends should see!",
        "source_title": "Private Thoughts"
    }
    
    post_id = None
    try:
        response = requests.post(f"{BACKEND_URL}/posts", json=post_data, headers=user1.get_headers())
        if response.status_code == 200:
            data = response.json()
            post_id = data.get("id")
            result.add_pass("POST /api/posts - Authenticated user created post")
            
            # Verify post fields
            if data.get("author_name") == user1.user_response["display_name"]:
                result.add_pass("POST /api/posts - Correct author name set")
            else:
                result.add_fail("Post author name", f"Wrong author name")
        else:
            result.add_fail("POST /api/posts - Auth user", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("POST /api/posts - Auth user", f"Request failed: {str(e)}")
    
    # User2 (friend) should see User1's post in their feed
    try:
        response = requests.get(f"{BACKEND_URL}/posts", headers=user2.get_headers())
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Look for User1's post
                found_post = any(post.get("author_id") == user1.user_response["id"] for post in data)
                if found_post:
                    result.add_pass("GET /api/posts - Friend can see friend's posts")
                else:
                    result.add_fail("Friend posts visibility", f"Friend's post not visible")
            else:
                result.add_fail("Friend feed", f"Expected list, got {type(data)}")
        else:
            result.add_fail("GET /api/posts - Friend feed", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/posts - Friend feed", f"Request failed: {str(e)}")
    
    # Test non-friend cannot see posts (if we have a third user)
    if len(user_sessions) >= 3:
        user3 = user_sessions[2]
        try:
            response = requests.get(f"{BACKEND_URL}/posts", headers=user3.get_headers())
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Should not see User1's posts
                    found_user1_post = any(post.get("author_id") == user1.user_response["id"] for post in data)
                    if not found_user1_post:
                        result.add_pass("GET /api/posts - Non-friend cannot see private posts")
                    else:
                        result.add_fail("Non-friend privacy", f"Non-friend can see private posts")
                else:
                    result.add_fail("Non-friend feed", f"Expected list, got {type(data)}")
            else:
                result.add_fail("GET /api/posts - Non-friend", f"Status code {response.status_code}")
        except Exception as e:
            result.add_fail("GET /api/posts - Non-friend", f"Request failed: {str(e)}")
    
    return post_id

def test_like_unlike_authenticated(result: TestResult, user_sessions: List[UserSession], post_id: str):
    """Test like/unlike functionality with authentication"""
    if not post_id or len(user_sessions) < 2:
        return
        
    user1, user2 = user_sessions[0], user_sessions[1]
    
    # User2 likes User1's post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/like", headers=user2.get_headers())
        if response.status_code == 200:
            data = response.json()
            if data.get("likes", 0) > 0 and data.get("liked_by_user") is True:
                result.add_pass("POST /api/posts/{id}/like - Authenticated like works")
            else:
                result.add_fail("Auth like", f"Like count or liked_by_user incorrect")
        else:
            result.add_fail("POST /api/posts/{id}/like - Auth", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/like - Auth", f"Request failed: {str(e)}")
    
    # User2 unlikes the post
    try:
        response = requests.post(f"{BACKEND_URL}/posts/{post_id}/unlike", headers=user2.get_headers())
        if response.status_code == 200:
            data = response.json()
            if data.get("liked_by_user") is False:
                result.add_pass("POST /api/posts/{id}/unlike - Authenticated unlike works")
            else:
                result.add_fail("Auth unlike", f"liked_by_user should be False")
        else:
            result.add_fail("POST /api/posts/{id}/unlike - Auth", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/posts/{id}/unlike - Auth", f"Request failed: {str(e)}")

def test_block_functionality(result: TestResult, user_sessions: List[UserSession]):
    """Test block/unblock functionality"""
    if len(user_sessions) < 3:
        return
        
    user1, user3 = user_sessions[0], user_sessions[2]
    
    # User1 blocks User3
    try:
        response = requests.post(f"{BACKEND_URL}/users/{user3.user_response['id']}/block", headers=user1.get_headers())
        if response.status_code == 200:
            result.add_pass("POST /api/users/{id}/block - User blocked successfully")
        else:
            result.add_fail("Block user", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("Block user", f"Request failed: {str(e)}")
    
    # Check blocked users list
    try:
        response = requests.get(f"{BACKEND_URL}/users/blocked", headers=user1.get_headers())
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                blocked_ids = [user["id"] for user in data]
                if user3.user_response["id"] in blocked_ids:
                    result.add_pass("GET /api/users/blocked - Blocked user in list")
                else:
                    result.add_fail("Blocked list", f"Blocked user not found in list")
            else:
                result.add_fail("Blocked list format", f"Expected list, got {type(data)}")
        else:
            result.add_fail("GET /api/users/blocked", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/users/blocked", f"Request failed: {str(e)}")
    
    # User1 unblocks User3
    try:
        response = requests.post(f"{BACKEND_URL}/users/{user3.user_response['id']}/unblock", headers=user1.get_headers())
        if response.status_code == 200:
            result.add_pass("POST /api/users/{id}/unblock - User unblocked successfully")
        else:
            result.add_fail("Unblock user", f"Status code {response.status_code}: {response.text}")
    except Exception as e:
        result.add_fail("Unblock user", f"Request failed: {str(e)}")

def test_friend_request_decline_and_cancel(result: TestResult, user_sessions: List[UserSession]):
    """Test friend request decline and cancel functionality"""
    if len(user_sessions) < 3:
        return
        
    user1, user3 = user_sessions[0], user_sessions[2]
    
    # User1 sends friend request to User3
    request_data = {"to_user_id": user3.user_response["id"]}
    try:
        response = requests.post(f"{BACKEND_URL}/friends/request", json=request_data, headers=user1.get_headers())
        if response.status_code == 200:
            result.add_pass("POST /api/friends/request - Second friend request sent")
        else:
            result.add_fail("Second friend request", f"Status code {response.status_code}")
            return
    except Exception as e:
        result.add_fail("Second friend request", f"Request failed: {str(e)}")
        return
    
    # User3 gets incoming requests and declines
    try:
        response = requests.get(f"{BACKEND_URL}/friends/requests/incoming", headers=user3.get_headers())
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                request_id = data[0]["id"]
                
                # Decline the request
                decline_response = requests.post(f"{BACKEND_URL}/friends/requests/{request_id}/decline", headers=user3.get_headers())
                if decline_response.status_code == 200:
                    result.add_pass("POST /api/friends/requests/{id}/decline - Request declined")
                else:
                    result.add_fail("Decline request", f"Status code {decline_response.status_code}")
            else:
                result.add_fail("Decline test setup", f"No incoming requests found")
        else:
            result.add_fail("Get requests for decline", f"Status code {response.status_code}")
    except Exception as e:
        result.add_fail("Decline request test", f"Request failed: {str(e)}")

def test_unauthorized_access(result: TestResult):
    """Test that endpoints requiring auth reject unauthorized requests"""
    unauthorized_endpoints = [
        ("GET", "/auth/me"),
        ("PUT", "/auth/profile"),
        ("GET", "/users/search?query=test"),
        ("POST", "/friends/request"),
        ("GET", "/friends/requests/incoming"),
        ("GET", "/friends"),
        ("POST", "/posts"),
        ("GET", "/posts")
    ]
    
    for method, endpoint in unauthorized_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BACKEND_URL}{endpoint}", json={})
            elif method == "PUT":
                response = requests.put(f"{BACKEND_URL}{endpoint}", json={})
                
            if response.status_code == 401:
                result.add_pass(f"{method} {endpoint} - Unauthorized access rejected")
            else:
                result.add_fail(f"Unauthorized {method} {endpoint}", f"Expected 401, got {response.status_code}")
        except Exception as e:
            result.add_fail(f"Unauthorized {method} {endpoint}", f"Request failed: {str(e)}")

def main():
    """Run all authentication and friend system tests"""
    print("🚀 Starting TextBlurb Authentication & Friend System Tests")
    print(f"Testing endpoint: {BACKEND_URL}")
    print("=" * 60)
    
    result = TestResult()
    
    # Test user registration
    user_sessions = test_user_registration(result)
    
    # Test duplicate registration
    if user_sessions:
        test_duplicate_registration(result, user_sessions[0].user_data)
    
    # Test user login
    user_sessions = test_user_login(result, user_sessions)
    
    # Test invalid login
    test_invalid_login(result)
    
    # Test get current user
    test_get_current_user(result, user_sessions)
    
    # Test profile update
    test_update_profile(result, user_sessions)
    
    # Test user search
    test_search_users(result, user_sessions)
    
    # Test friend request flow
    friends_info = test_friend_request_flow(result, user_sessions)
    
    # Test posts with authentication and friends
    post_id = test_posts_with_friends(result, user_sessions, friends_info)
    
    # Test like/unlike with authentication
    test_like_unlike_authenticated(result, user_sessions, post_id)
    
    # Test block functionality
    test_block_functionality(result, user_sessions)
    
    # Test friend request decline
    test_friend_request_decline_and_cancel(result, user_sessions)
    
    # Test unauthorized access
    test_unauthorized_access(result)
    
    # Print summary
    success = result.summary()
    
    if success:
        print("\n🎉 All authentication and friend system tests passed! Backend API is working correctly.")
    else:
        print(f"\n⚠️  {result.failed} test(s) failed. Please check the issues above.")
    
    return success

if __name__ == "__main__":
    main()