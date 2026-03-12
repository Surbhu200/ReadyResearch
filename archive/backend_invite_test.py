#!/usr/bin/env python3
"""
Comprehensive backend API tests for TextBlurb invite link system.
Tests all invite endpoints following the requested test flow.
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
        "email": f"inviteuser{suffix}{random_num}@textblurb.com",
        "password": "secure123456",
        "display_name": f"Invite Test User{suffix}",
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

def test_get_my_invite_link(result: TestResult, token: str, user_id: str, display_name: str) -> Optional[str]:
    """Test GET /api/invite/my-link - Get/generate user's invite link"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/invite/my-link", headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["invite_code", "invite_url", "user_id", "display_name"]
            
            if all(field in data for field in required_fields):
                result.add_pass("GET /api/invite/my-link - Returns all required fields")
                
                # Verify user_id matches
                if data["user_id"] == user_id:
                    result.add_pass("GET /api/invite/my-link - User ID matches")
                else:
                    result.add_fail("GET /api/invite/my-link - User ID", f"Expected {user_id}, got {data['user_id']}")
                
                # Verify display_name matches
                if data["display_name"] == display_name:
                    result.add_pass("GET /api/invite/my-link - Display name matches")
                else:
                    result.add_fail("GET /api/invite/my-link - Display name", f"Expected {display_name}, got {data['display_name']}")
                
                # Verify invite_code is present and not empty
                if data["invite_code"] and len(data["invite_code"]) > 0:
                    result.add_pass("GET /api/invite/my-link - Invite code generated")
                    return data["invite_code"]
                else:
                    result.add_fail("GET /api/invite/my-link - Invite code", f"Empty or missing invite code")
                    return None
                
            else:
                missing = [f for f in required_fields if f not in data]
                result.add_fail("GET /api/invite/my-link", f"Missing fields: {missing}")
                return None
        else:
            result.add_fail("GET /api/invite/my-link", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.add_fail("GET /api/invite/my-link", f"Request failed: {str(e)}")
        return None

def test_get_my_invite_link_unauthorized(result: TestResult):
    """Test GET /api/invite/my-link without authorization"""
    try:
        response = requests.get(f"{BACKEND_URL}/invite/my-link")
        if response.status_code == 401:
            result.add_pass("GET /api/invite/my-link - Requires authorization")
        else:
            result.add_fail("GET /api/invite/my-link - Auth", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/invite/my-link - Auth", f"Request failed: {str(e)}")

def test_regenerate_invite_link(result: TestResult, token: str, old_invite_code: str) -> Optional[str]:
    """Test POST /api/invite/regenerate - Generate new invite code"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BACKEND_URL}/invite/regenerate", headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["invite_code", "invite_url", "user_id", "display_name"]
            
            if all(field in data for field in required_fields):
                result.add_pass("POST /api/invite/regenerate - Returns all required fields")
                
                # Verify new invite code is different from old one
                if data["invite_code"] != old_invite_code:
                    result.add_pass("POST /api/invite/regenerate - New invite code generated")
                    return data["invite_code"]
                else:
                    result.add_fail("POST /api/invite/regenerate - New code", f"Same invite code returned")
                    return None
            else:
                missing = [f for f in required_fields if f not in data]
                result.add_fail("POST /api/invite/regenerate", f"Missing fields: {missing}")
                return None
        else:
            result.add_fail("POST /api/invite/regenerate", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.add_fail("POST /api/invite/regenerate", f"Request failed: {str(e)}")
        return None

def test_regenerate_invite_unauthorized(result: TestResult):
    """Test POST /api/invite/regenerate without authorization"""
    try:
        response = requests.post(f"{BACKEND_URL}/invite/regenerate")
        if response.status_code == 401:
            result.add_pass("POST /api/invite/regenerate - Requires authorization")
        else:
            result.add_fail("POST /api/invite/regenerate - Auth", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/invite/regenerate - Auth", f"Request failed: {str(e)}")

def test_get_invite_info(result: TestResult, token: str, invite_code: str, inviter_user_id: str, inviter_display_name: str, is_self: bool = False):
    """Test GET /api/invite/{invite_code} - Get info about an invite"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/invite/{invite_code}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["invite_code", "user_id", "display_name", "posts_count", "friends_count", "is_already_friend", "is_self", "request_pending"]
            
            if all(field in data for field in required_fields):
                result.add_pass("GET /api/invite/{code} - Returns all required fields")
                
                # Verify invite_code matches
                if data["invite_code"] == invite_code:
                    result.add_pass("GET /api/invite/{code} - Invite code matches")
                else:
                    result.add_fail("GET /api/invite/{code} - Code", f"Expected {invite_code}, got {data['invite_code']}")
                
                # Verify user_id matches inviter
                if data["user_id"] == inviter_user_id:
                    result.add_pass("GET /api/invite/{code} - User ID matches inviter")
                else:
                    result.add_fail("GET /api/invite/{code} - User ID", f"Expected {inviter_user_id}, got {data['user_id']}")
                
                # Verify display_name matches inviter
                if data["display_name"] == inviter_display_name:
                    result.add_pass("GET /api/invite/{code} - Display name matches inviter")
                else:
                    result.add_fail("GET /api/invite/{code} - Display name", f"Expected {inviter_display_name}, got {data['display_name']}")
                
                # Verify is_self flag
                if data["is_self"] == is_self:
                    result.add_pass(f"GET /api/invite/{{code}} - is_self={is_self} correct")
                else:
                    result.add_fail("GET /api/invite/{code} - is_self", f"Expected {is_self}, got {data['is_self']}")
                
                # Verify counts are non-negative integers
                if isinstance(data["posts_count"], int) and data["posts_count"] >= 0:
                    result.add_pass("GET /api/invite/{code} - Posts count valid")
                else:
                    result.add_fail("GET /api/invite/{code} - Posts count", f"Invalid posts_count: {data['posts_count']}")
                
                if isinstance(data["friends_count"], int) and data["friends_count"] >= 0:
                    result.add_pass("GET /api/invite/{code} - Friends count valid")
                else:
                    result.add_fail("GET /api/invite/{code} - Friends count", f"Invalid friends_count: {data['friends_count']}")
                
                return data
            else:
                missing = [f for f in required_fields if f not in data]
                result.add_fail("GET /api/invite/{code}", f"Missing fields: {missing}")
                return None
        else:
            result.add_fail("GET /api/invite/{code}", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        result.add_fail("GET /api/invite/{code}", f"Request failed: {str(e)}")
        return None

def test_get_invite_info_invalid_code(result: TestResult, token: str):
    """Test GET /api/invite/{invite_code} with invalid code"""
    headers = {"Authorization": f"Bearer {token}"}
    invalid_code = "invalid123"
    
    try:
        response = requests.get(f"{BACKEND_URL}/invite/{invalid_code}", headers=headers)
        if response.status_code == 404:
            result.add_pass("GET /api/invite/{code} - 404 for invalid invite code")
        else:
            result.add_fail("GET /api/invite/{code} - Invalid", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/invite/{code} - Invalid", f"Request failed: {str(e)}")

def test_get_invite_info_unauthorized(result: TestResult, invite_code: str):
    """Test GET /api/invite/{invite_code} without authorization"""
    try:
        response = requests.get(f"{BACKEND_URL}/invite/{invite_code}")
        if response.status_code == 401:
            result.add_pass("GET /api/invite/{code} - Requires authorization")
        else:
            result.add_fail("GET /api/invite/{code} - Auth", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.add_fail("GET /api/invite/{code} - Auth", f"Request failed: {str(e)}")

def test_accept_invite(result: TestResult, token: str, invite_code: str, inviter_display_name: str) -> bool:
    """Test POST /api/invite/{invite_code}/accept - Accept invite and become friends"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BACKEND_URL}/invite/{invite_code}/accept", headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if "message" in data and "status" in data:
                result.add_pass("POST /api/invite/{code}/accept - Returns success response")
                
                # Check success status
                if data["status"] == "success":
                    result.add_pass("POST /api/invite/{code}/accept - Status is success")
                    
                    # Check friend info in response
                    if "friend" in data and "display_name" in data["friend"]:
                        if data["friend"]["display_name"] == inviter_display_name:
                            result.add_pass("POST /api/invite/{code}/accept - Friend info correct")
                        else:
                            result.add_fail("POST /api/invite/{code}/accept - Friend info", f"Wrong display_name in response")
                    else:
                        result.add_fail("POST /api/invite/{code}/accept - Friend info", f"Missing friend info in response")
                    
                    return True
                elif data["status"] == "already_friends":
                    result.add_pass("POST /api/invite/{code}/accept - Already friends status")
                    return True
                else:
                    result.add_fail("POST /api/invite/{code}/accept - Status", f"Unknown status: {data['status']}")
                    return False
            else:
                result.add_fail("POST /api/invite/{code}/accept", f"Missing message or status in response")
                return False
        else:
            result.add_fail("POST /api/invite/{code}/accept", f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        result.add_fail("POST /api/invite/{code}/accept", f"Request failed: {str(e)}")
        return False

def test_accept_own_invite(result: TestResult, token: str, own_invite_code: str):
    """Test POST /api/invite/{invite_code}/accept with own invite code (should fail)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BACKEND_URL}/invite/{own_invite_code}/accept", headers=headers)
        if response.status_code == 400:
            result.add_pass("POST /api/invite/{code}/accept - Cannot accept own invite")
        else:
            result.add_fail("POST /api/invite/{code}/accept - Own invite", f"Expected 400, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/invite/{code}/accept - Own invite", f"Request failed: {str(e)}")

def test_accept_invalid_invite(result: TestResult, token: str):
    """Test POST /api/invite/{invite_code}/accept with invalid code"""
    headers = {"Authorization": f"Bearer {token}"}
    invalid_code = "invalid123"
    
    try:
        response = requests.post(f"{BACKEND_URL}/invite/{invalid_code}/accept", headers=headers)
        if response.status_code == 404:
            result.add_pass("POST /api/invite/{code}/accept - 404 for invalid invite code")
        else:
            result.add_fail("POST /api/invite/{code}/accept - Invalid", f"Expected 404, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/invite/{code}/accept - Invalid", f"Request failed: {str(e)}")

def test_accept_invite_unauthorized(result: TestResult, invite_code: str):
    """Test POST /api/invite/{invite_code}/accept without authorization"""
    try:
        response = requests.post(f"{BACKEND_URL}/invite/{invite_code}/accept")
        if response.status_code == 401:
            result.add_pass("POST /api/invite/{code}/accept - Requires authorization")
        else:
            result.add_fail("POST /api/invite/{code}/accept - Auth", f"Expected 401, got {response.status_code}")
    except Exception as e:
        result.add_fail("POST /api/invite/{code}/accept - Auth", f"Request failed: {str(e)}")

def verify_friendship(result: TestResult, user1_token: str, user2_token: str, user1_id: str, user2_id: str):
    """Verify that two users are now friends"""
    
    # Check User1's friends list
    try:
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        response1 = requests.get(f"{BACKEND_URL}/friends", headers=headers1)
        if response1.status_code == 200:
            friends1 = response1.json()
            friend_ids1 = [friend["id"] for friend in friends1] if isinstance(friends1, list) else []
            
            if user2_id in friend_ids1:
                result.add_pass("Friendship verification - User1 has User2 as friend")
            else:
                result.add_fail("Friendship verification - User1", f"User2 not found in User1's friends list")
        else:
            result.add_fail("Friendship verification - User1", f"Failed to get friends list: {response1.status_code}")
    except Exception as e:
        result.add_fail("Friendship verification - User1", f"Request failed: {str(e)}")
    
    # Check User2's friends list
    try:
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        response2 = requests.get(f"{BACKEND_URL}/friends", headers=headers2)
        if response2.status_code == 200:
            friends2 = response2.json()
            friend_ids2 = [friend["id"] for friend in friends2] if isinstance(friends2, list) else []
            
            if user1_id in friend_ids2:
                result.add_pass("Friendship verification - User2 has User1 as friend")
            else:
                result.add_fail("Friendship verification - User2", f"User1 not found in User2's friends list")
        else:
            result.add_fail("Friendship verification - User2", f"Failed to get friends list: {response2.status_code}")
    except Exception as e:
        result.add_fail("Friendship verification - User2", f"Request failed: {str(e)}")

def main():
    """Run the complete invite link system test flow"""
    print("🚀 Starting TextBlurb Invite Link System Tests")
    print(f"Testing endpoint: {BACKEND_URL}")
    print("Testing invite system endpoints following the requested test flow")
    print("=" * 80)
    
    result = TestResult()
    
    # Test unauthorized access first
    print("\n🔒 Testing authorization requirements...")
    test_get_my_invite_link_unauthorized(result)
    test_regenerate_invite_unauthorized(result)
    
    # Step 1: Create User A and User B
    print("\n👥 Step 1: Creating test users...")
    user_a_id, user_a_token, user_a_name = create_test_user(result, "A")
    user_b_id, user_b_token, user_b_name = create_test_user(result, "B")
    
    if not user_a_token or not user_b_token:
        print("❌ Failed to create test users. Cannot continue with invite tests.")
        result.summary()
        return False
    
    # Create some posts for the users to have stats
    print("\n📝 Creating test posts for user stats...")
    post_a1 = create_test_post(result, user_a_token, "Amazing insight about life and productivity!", "A1")
    post_a2 = create_test_post(result, user_a_token, "Another brilliant thought from User A!", "A2")
    post_b1 = create_test_post(result, user_b_token, "User B's perspective on success and growth!", "B1")
    
    # Step 2: User A gets their invite link
    print("\n🔗 Step 2: User A getting their invite link...")
    user_a_invite_code = test_get_my_invite_link(result, user_a_token, user_a_id, user_a_name)
    
    if not user_a_invite_code:
        print("❌ Failed to get User A's invite code. Cannot continue with invite tests.")
        result.summary()
        return False
    
    # Test regenerate invite link
    print("\n🔄 Testing invite link regeneration...")
    new_user_a_invite_code = test_regenerate_invite_link(result, user_a_token, user_a_invite_code)
    if new_user_a_invite_code:
        user_a_invite_code = new_user_a_invite_code  # Use the new code for further tests
    
    # Step 3: User B checks invite info (should show is_already_friend=false)
    print("\n👀 Step 3: User B checking invite info before accepting...")
    invite_info_before = test_get_invite_info(result, user_b_token, user_a_invite_code, user_a_id, user_a_name, is_self=False)
    
    if invite_info_before:
        # Verify is_already_friend is false initially
        if not invite_info_before.get("is_already_friend"):
            result.add_pass("Invite info - is_already_friend=false before accepting")
        else:
            result.add_fail("Invite info - Before accept", f"Expected is_already_friend=false, got {invite_info_before.get('is_already_friend')}")
    
    # Test User A checking their own invite (should show is_self=true)
    print("\n🪞 Testing User A checking own invite info...")
    own_invite_info = test_get_invite_info(result, user_a_token, user_a_invite_code, user_a_id, user_a_name, is_self=True)
    
    # Test error cases
    print("\n❌ Testing error cases...")
    test_get_invite_info_invalid_code(result, user_b_token)
    test_get_invite_info_unauthorized(result, user_a_invite_code)
    test_accept_own_invite(result, user_a_token, user_a_invite_code)
    test_accept_invalid_invite(result, user_b_token)
    test_accept_invite_unauthorized(result, user_a_invite_code)
    
    # Step 4: User B accepts the invite
    print("\n🤝 Step 4: User B accepting the invite...")
    accept_success = test_accept_invite(result, user_b_token, user_a_invite_code, user_a_name)
    
    if accept_success:
        # Step 5: Verify they are now friends
        print("\n✅ Step 5: Verifying friendship was established...")
        verify_friendship(result, user_a_token, user_b_token, user_a_id, user_b_id)
        
        # Step 6: User B checks invite info again (should show is_already_friend=true)
        print("\n🔄 Step 6: User B checking invite info after accepting...")
        invite_info_after = test_get_invite_info(result, user_b_token, user_a_invite_code, user_a_id, user_a_name, is_self=False)
        
        if invite_info_after:
            # Verify is_already_friend is now true
            if invite_info_after.get("is_already_friend"):
                result.add_pass("Invite info - is_already_friend=true after accepting")
            else:
                result.add_fail("Invite info - After accept", f"Expected is_already_friend=true, got {invite_info_after.get('is_already_friend')}")
        
        # Step 7: Test User B accepting the same invite again (should show already_friends)
        print("\n🔁 Step 7: Testing accepting invite again (already friends)...")
        test_accept_invite(result, user_b_token, user_a_invite_code, user_a_name)
    
    # Print summary
    success = result.summary()
    
    if success:
        print("\n🎉 All invite link system tests passed! Invite functionality is working correctly.")
        print("\n✨ Test flow completed successfully:")
        print("   ✅ User A can generate and regenerate invite links")
        print("   ✅ User B can view invite information before accepting")
        print("   ✅ User B can accept invite and become friends instantly")
        print("   ✅ Friendship is properly established in both directions")
        print("   ✅ Invite info correctly reflects friendship status")
        print("   ✅ Error cases handled properly (invalid codes, own invites, unauthorized access)")
    else:
        print(f"\n⚠️  {result.failed} test(s) failed. Please check the issues above.")
    
    return success

if __name__ == "__main__":
    main()